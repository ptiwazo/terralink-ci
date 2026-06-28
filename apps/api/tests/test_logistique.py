"""Tests de la logistique sécurisée (Phase 3) : transporteurs, code de remise,
GPS, litige. Livrable §7 : confirmation seulement avec le bon code ; un litige
bloque la libération des fonds.
"""
from app.services import ledger_service
from app.services.ledger_service import COMPTE_COMMISSION, COMPTE_ESCROW
from tests.conftest import (
    assigner_transporteur,
    confirmer_reception,
    creer_interne,
    creer_offre,
    creer_transporteur_valide,
    creer_utilisateur,
    livrer_comptant,
    payer_commande,
)


def _commande_payee(client, produit_id, prix=500, qte=2):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=100, prix=prix)
    ach = creer_utilisateur(client, "ACHETEUR")
    cmd = client.post(
        "/api/v1/commandes",
        headers=ach["headers"],
        json={"lignes": [{"offre_id": offre["id"], "quantite": qte}]},
    ).json()
    payer_commande(client, ach["headers"], cmd["id"])
    client.post(
        f"/api/v1/commandes/{cmd['id']}/transition",
        headers=prod["headers"],
        json={"action": "PREPARER"},
    )
    return prod, ach, cmd


def _expedier(client, prod_headers, cid):
    return client.post(
        f"/api/v1/commandes/{cid}/transition",
        headers=prod_headers,
        json={"action": "EXPEDIER"},
    )


# --- Transporteurs ---

def test_profil_transporteur_et_validation(client, db_session):
    transp = creer_utilisateur(client, "TRANSPORTEUR")
    r = client.post(
        "/api/v1/transporteurs/profil",
        headers=transp["headers"],
        json={"vehicule": "Camion", "immatriculation": "CI-9", "caution_deposee": 50000},
    )
    assert r.status_code == 201 and r.json()["statut"] == "EN_ATTENTE"
    tid = r.json()["id"]
    ops = creer_interne(db_session, "OPS")
    v = client.post(f"/api/v1/transporteurs/{tid}/valider", headers=ops["headers"])
    assert v.status_code == 200 and v.json()["statut"] == "VALIDE"


def test_non_transporteur_refuse(client, produit_id):
    ach = creer_utilisateur(client, "ACHETEUR")
    r = client.post(
        "/api/v1/transporteurs/profil",
        headers=ach["headers"],
        json={"vehicule": "X", "immatriculation": "Y", "caution_deposee": 0},
    )
    assert r.status_code == 403


# --- Assignation + code de remise ---

def test_assignation_transporteur_non_valide_refusee(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    transp = creer_utilisateur(client, "TRANSPORTEUR")
    prof = client.post(
        "/api/v1/transporteurs/profil",
        headers=transp["headers"],
        json={"vehicule": "Moto", "immatriculation": "CI-7", "caution_deposee": 0},
    ).json()
    # Pas validé → assignation refusée.
    r = client.post(
        f"/api/v1/commandes/{cmd['id']}/assigner-transporteur",
        headers=prod["headers"],
        json={"transporteur_id": prof["id"]},
    )
    assert r.status_code == 409


def test_expedier_sans_transporteur_refuse(client, produit_id):
    prod, ach, cmd = _commande_payee(client, produit_id)
    r = _expedier(client, prod["headers"], cmd["id"])
    assert r.status_code == 409


def test_double_assignation_refusee(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    transp = creer_transporteur_valide(client, db_session)
    assigner_transporteur(client, prod["headers"], cmd["id"], transp["transporteur_id"])
    r = client.post(
        f"/api/v1/commandes/{cmd['id']}/assigner-transporteur",
        headers=prod["headers"],
        json={"transporteur_id": transp["transporteur_id"]},
    )
    assert r.status_code == 409


# --- Code de remise : LE garde-fou ---

def test_confirmation_mauvais_code_bloque(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    cid = cmd["id"]
    transp = creer_transporteur_valide(client, db_session)
    assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    _expedier(client, prod["headers"], cid)

    r = confirmer_reception(client, ach["headers"], cid, "000000")
    assert r.status_code == 403  # mauvais code → refusé

    # Les fonds restent séquestrés, commande toujours EN_LIVRAISON.
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 1000
    statut = client.get(f"/api/v1/commandes/{cid}", headers=ach["headers"]).json()["statut"]
    assert statut == "EN_LIVRAISON"


def test_confirmation_bon_code_libere(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    cid = cmd["id"]
    transp = creer_transporteur_valide(client, db_session)
    code = assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    _expedier(client, prod["headers"], cid)

    r = confirmer_reception(client, ach["headers"], cid, code)
    assert r.status_code == 200 and r.json()["statut"] == "FONDS_LIBERES"
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 0
    assert ledger_service.solde(db_session, COMPTE_COMMISSION) == 50
    assert ledger_service.solde_global(db_session) == 0


# --- Traçabilité GPS ---

def test_mes_courses_transporteur(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    cid = cmd["id"]
    transp = creer_transporteur_valide(client, db_session)
    assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    _expedier(client, prod["headers"], cid)

    courses = client.get("/api/v1/transporteurs/mes-courses", headers=transp["headers"]).json()
    assert len(courses) == 1
    assert courses[0]["commande_id"] == cid
    assert courses[0]["livraison"]["statut"] == "EN_COURS"
    assert "×" in courses[0]["produits"]


def test_notation_transporteur(client, produit_id, db_session):
    res = livrer_comptant(client, db_session, produit_id)  # livrée -> FONDS_LIBERES
    r = client.post(
        f"/api/v1/commandes/{res['cid']}/noter-transporteur",
        headers=res["ach"]["headers"],
        json={"note": 5},
    )
    assert r.status_code == 200 and r.json()["note_transporteur"] == 5


def test_notation_avant_livraison_refusee(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)  # pas encore livrée
    r = client.post(
        f"/api/v1/commandes/{cmd['id']}/noter-transporteur",
        headers=ach["headers"],
        json={"note": 4},
    )
    assert r.status_code == 409


def test_notation_par_autre_refusee(client, produit_id, db_session):
    res = livrer_comptant(client, db_session, produit_id)
    autre = creer_utilisateur(client, "ACHETEUR")
    r = client.post(
        f"/api/v1/commandes/{res['cid']}/noter-transporteur",
        headers=autre["headers"],
        json={"note": 5},
    )
    assert r.status_code == 403


def test_position_par_transporteur_assigne(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    cid = cmd["id"]
    transp = creer_transporteur_valide(client, db_session)
    assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    _expedier(client, prod["headers"], cid)

    r = client.post(
        f"/api/v1/commandes/{cid}/position",
        headers=transp["headers"],
        json={"lat": 5.34, "lng": -4.02},
    )
    assert r.status_code == 200 and len(r.json()["gps_traces"]) == 1
    # Un autre acheteur ne peut pas tracer.
    autre = creer_utilisateur(client, "ACHETEUR")
    r2 = client.post(
        f"/api/v1/commandes/{cid}/position", headers=autre["headers"], json={"lat": 1, "lng": 1}
    )
    assert r2.status_code == 403


# --- Litige ---

def test_litige_bloque_liberation_puis_remboursement(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    cid = cmd["id"]
    transp = creer_transporteur_valide(client, db_session)
    code = assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    _expedier(client, prod["headers"], cid)

    # L'acheteur signale un litige.
    lit = client.post(
        f"/api/v1/commandes/{cid}/transition",
        headers=ach["headers"],
        json={"action": "SIGNALER_LITIGE"},
    )
    assert lit.status_code == 200 and lit.json()["statut"] == "LITIGE"

    # La confirmation (même avec le bon code) est désormais impossible : litige bloque.
    r = confirmer_reception(client, ach["headers"], cid, code)
    assert r.status_code == 409
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 1000  # toujours séquestré

    # OPS résout en remboursant l'acheteur.
    ops = creer_interne(db_session, "OPS")
    res = client.post(
        f"/api/v1/commandes/{cid}/resoudre", headers=ops["headers"], json={"sens": "REMBOURSE"}
    )
    assert res.status_code == 200 and res.json()["statut"] == "RESOLUE_REMBOURSEE"
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 0
    assert ledger_service.solde(db_session, COMPTE_COMMISSION) == 0  # pas de commission
    assert ledger_service.solde_global(db_session) == 0


def test_litige_resolu_en_liberation(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    cid = cmd["id"]
    transp = creer_transporteur_valide(client, db_session)
    assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    _expedier(client, prod["headers"], cid)
    client.post(
        f"/api/v1/commandes/{cid}/transition",
        headers=ach["headers"],
        json={"action": "SIGNALER_LITIGE"},
    )
    ops = creer_interne(db_session, "OPS")
    res = client.post(
        f"/api/v1/commandes/{cid}/resoudre", headers=ops["headers"], json={"sens": "LIBERE"}
    )
    assert res.status_code == 200 and res.json()["statut"] == "RESOLUE_LIBEREE"
    assert ledger_service.solde(db_session, COMPTE_COMMISSION) == 50
    assert ledger_service.solde_global(db_session) == 0


def test_resolution_reserve_aux_ops(client, produit_id, db_session):
    prod, ach, cmd = _commande_payee(client, produit_id)
    cid = cmd["id"]
    transp = creer_transporteur_valide(client, db_session)
    assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    _expedier(client, prod["headers"], cid)
    client.post(
        f"/api/v1/commandes/{cid}/transition",
        headers=ach["headers"],
        json={"action": "SIGNALER_LITIGE"},
    )
    # L'acheteur ne peut pas résoudre.
    r = client.post(
        f"/api/v1/commandes/{cid}/resoudre", headers=ach["headers"], json={"sens": "REMBOURSE"}
    )
    assert r.status_code == 403
