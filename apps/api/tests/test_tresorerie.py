"""Tests trésorerie / paiement différé (CLAUDE.md §4, §7, Phase 4).

Prouvent : éligibilité/scoring, octroi d'avance (producteur payé, créance
ouverte), comptabilisation correcte (solde global = 0), remboursement, impayés,
plafond de crédit respecté, et résolution de litige sur commande différée.
"""
import uuid
from datetime import datetime, timedelta, timezone

from app.models.avance import AvanceTresorerie
from app.models.enums import AvanceStatut
from app.services import ledger_service
from app.services.ledger_service import (
    COMPTE_COMMISSION,
    COMPTE_DECOTE,
    COMPTE_PERTES,
    compte_creance,
)
from tests.conftest import (
    assigner_transporteur,
    confirmer_reception,
    creer_interne,
    creer_offre,
    creer_transporteur_valide,
    creer_utilisateur,
    payer_commande,
)


def _acheteur_avec_credit(client, db_session, plafond=1_000_000):
    ach = creer_utilisateur(client, "ACHETEUR")
    client.post("/api/v1/acheteurs/profil", headers=ach["headers"], json={"type": "RESTAURANT"})
    ops = creer_interne(db_session, "OPS")
    r = client.post(
        f"/api/v1/acheteurs/{ach['user']['id']}/plafond",
        headers=ops["headers"],
        json={"plafond_credit": plafond},
    )
    assert r.status_code == 200, r.text
    return ach, ops


def _offre(client, produit_id, prix=500, qte=100):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=qte, prix=prix)
    return prod, offre


def _commander_differe(client, ach_headers, offre_id, quantite):
    return client.post(
        "/api/v1/commandes",
        headers=ach_headers,
        json={"lignes": [{"offre_id": offre_id, "quantite": quantite}], "mode_paiement": "DIFFERE"},
    )


def test_differe_refuse_sans_credit(client, produit_id):
    prod, offre = _offre(client, produit_id)
    ach = creer_utilisateur(client, "ACHETEUR")  # aucun crédit
    r = _commander_differe(client, ach["headers"], offre["id"], 2)
    assert r.status_code == 403


def test_octroi_avance_et_ledger(client, produit_id, db_session):
    prod, offre = _offre(client, produit_id, prix=1000)
    ach, _ = _acheteur_avec_credit(client, db_session)
    r = _commander_differe(client, ach["headers"], offre["id"], 5)  # 5000 FCFA
    assert r.status_code == 201, r.text
    cmd = r.json()
    assert cmd["statut"] == "AVANCE_VERSEE"

    avance = client.get(f"/api/v1/commandes/{cmd['id']}/avance", headers=ach["headers"]).json()
    # commission 5% = 250, décote 2% = 100, avance = 4650
    assert avance["commission"] == 250
    assert avance["decote"] == 100
    assert avance["montant_avance"] == 4650
    assert avance["statut"] == "AVANCEE"

    cc = compte_creance(uuid.UUID(ach["user"]["id"]))
    assert ledger_service.solde(db_session, cc) == -5000  # l'acheteur doit 5000
    assert ledger_service.solde(db_session, COMPTE_COMMISSION) == 250
    assert ledger_service.solde(db_session, COMPTE_DECOTE) == 100
    assert ledger_service.solde_global(db_session) == 0


def test_plafond_respecte(client, produit_id, db_session):
    prod, offre = _offre(client, produit_id, prix=1000)
    ach, _ = _acheteur_avec_credit(client, db_session, plafond=3000)
    # 4 * 1000 = 4000 > plafond 3000 → refusé.
    r = _commander_differe(client, ach["headers"], offre["id"], 4)
    assert r.status_code == 403
    # 2 * 1000 = 2000 ≤ 3000 → accepté.
    assert _commander_differe(client, ach["headers"], offre["id"], 2).status_code == 201


def test_eligibilite_basee_sur_historique_comptant(client, produit_id, db_session):
    """Une commande comptant menée à terme augmente le plafond suggéré (scoring)."""
    prod, offre = _offre(client, produit_id, prix=1000, qte=100)
    ach = creer_utilisateur(client, "ACHETEUR")
    # Cycle comptant complet -> FONDS_LIBERES.
    cmd = client.post(
        "/api/v1/commandes",
        headers=ach["headers"],
        json={"lignes": [{"offre_id": offre["id"], "quantite": 2}]},
    ).json()
    payer_commande(client, ach["headers"], cmd["id"])
    client.post(f"/api/v1/commandes/{cmd['id']}/transition", headers=prod["headers"], json={"action": "PREPARER"})
    transp = creer_transporteur_valide(client, db_session)
    code = assigner_transporteur(client, prod["headers"], cmd["id"], transp["transporteur_id"])
    client.post(f"/api/v1/commandes/{cmd['id']}/transition", headers=prod["headers"], json={"action": "EXPEDIER"})
    confirmer_reception(client, ach["headers"], cmd["id"], code)

    elig = client.get("/api/v1/acheteurs/mon-eligibilite", headers=ach["headers"]).json()
    assert elig["score"] == 1
    assert elig["plafond_suggere"] == 100000  # credit_unit
    assert elig["disponible"] == 100000
    # Sans plafond manuel, le différé est désormais possible grâce au scoring.
    assert _commander_differe(client, ach["headers"], offre["id"], 3).status_code == 201


def test_remboursement_creance(client, produit_id, db_session):
    prod, offre = _offre(client, produit_id, prix=1000)
    ach, _ = _acheteur_avec_credit(client, db_session)
    cmd = _commander_differe(client, ach["headers"], offre["id"], 3).json()  # 3000
    cid = cmd["id"]
    cc = compte_creance(uuid.UUID(ach["user"]["id"]))
    assert ledger_service.solde(db_session, cc) == -3000

    r = client.post(f"/api/v1/commandes/{cid}/rembourser-creance", headers=ach["headers"])
    assert r.status_code == 200 and r.json()["statut"] == "REMBOURSEE"
    assert ledger_service.solde(db_session, cc) == 0  # créance soldée
    assert ledger_service.solde_global(db_session) == 0


def test_differe_cycle_complet_puis_cloture(client, produit_id, db_session):
    prod, offre = _offre(client, produit_id, prix=1000)
    ach, _ = _acheteur_avec_credit(client, db_session)
    cmd = _commander_differe(client, ach["headers"], offre["id"], 2).json()
    cid = cmd["id"]
    client.post(f"/api/v1/commandes/{cid}/transition", headers=prod["headers"], json={"action": "PREPARER"})
    transp = creer_transporteur_valide(client, db_session)
    code = assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    client.post(f"/api/v1/commandes/{cid}/transition", headers=prod["headers"], json={"action": "EXPEDIER"})
    # DIFFERE : la confirmation ne libère pas de fonds (producteur déjà payé).
    r = confirmer_reception(client, ach["headers"], cid, code)
    assert r.status_code == 200 and r.json()["statut"] == "LIVREE_CONFORME"
    # Remboursement de la créance -> CLOTUREE.
    rb = client.post(f"/api/v1/commandes/{cid}/rembourser-creance", headers=ach["headers"])
    assert rb.status_code == 200
    statut = client.get(f"/api/v1/commandes/{cid}", headers=ach["headers"]).json()["statut"]
    assert statut == "CLOTUREE"
    assert ledger_service.solde_global(db_session) == 0


def test_impayes(client, produit_id, db_session):
    prod, offre = _offre(client, produit_id, prix=1000)
    ach, ops = _acheteur_avec_credit(client, db_session)
    cmd = _commander_differe(client, ach["headers"], offre["id"], 2).json()
    # Forcer l'échéance dans le passé.
    db_session.execute(
        AvanceTresorerie.__table__.update()
        .where(AvanceTresorerie.commande_id == uuid.UUID(cmd["id"]))
        .values(echeance=datetime.now(timezone.utc) - timedelta(days=1))
    )
    db_session.commit()

    r = client.post("/api/v1/tresorerie/marquer-impayes", headers=ops["headers"])
    assert r.status_code == 200 and r.json()["impayes_marques"] >= 1
    impayes = client.get("/api/v1/tresorerie/impayes", headers=ops["headers"]).json()
    assert any(i["commande_id"] == cmd["id"] for i in impayes)


def test_litige_differe_annule_creance(client, produit_id, db_session):
    prod, offre = _offre(client, produit_id, prix=1000)
    ach, ops = _acheteur_avec_credit(client, db_session)
    cmd = _commander_differe(client, ach["headers"], offre["id"], 2).json()  # 2000
    cid = cmd["id"]
    client.post(f"/api/v1/commandes/{cid}/transition", headers=prod["headers"], json={"action": "PREPARER"})
    transp = creer_transporteur_valide(client, db_session)
    assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    client.post(f"/api/v1/commandes/{cid}/transition", headers=prod["headers"], json={"action": "EXPEDIER"})
    client.post(f"/api/v1/commandes/{cid}/transition", headers=ach["headers"], json={"action": "SIGNALER_LITIGE"})

    res = client.post(f"/api/v1/commandes/{cid}/resoudre", headers=ops["headers"], json={"sens": "REMBOURSE"})
    assert res.status_code == 200 and res.json()["statut"] == "RESOLUE_REMBOURSEE"

    cc = compte_creance(uuid.UUID(ach["user"]["id"]))
    assert ledger_service.solde(db_session, cc) == 0  # créance éteinte
    # commission/décote annulées, perte = avance versée.
    assert ledger_service.solde(db_session, COMPTE_COMMISSION) == 0
    assert ledger_service.solde(db_session, COMPTE_DECOTE) == 0
    # avance versée = 2000 - commission(100) - décote(40) = 1860 → perte.
    assert ledger_service.solde(db_session, COMPTE_PERTES) == -1860
    assert ledger_service.solde_global(db_session) == 0
