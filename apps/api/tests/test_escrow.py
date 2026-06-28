"""Tests du cycle escrow (CLAUDE.md §2.1, §6, Phase 2).

Prouvent : séquestre correct, libération avec commission, **le solde global ne
fuit jamais (= 0)**, idempotence (double webhook / double paiement sans effet),
double validation des montants, et rejet de signature invalide.
"""
import uuid

from app.models.enums import EscrowStatut
from app.models.escrow import EscrowTransaction
from app.payments.sandbox import SandboxProvider
from app.services import escrow_service, ledger_service
from app.services.ledger_service import (
    COMPTE_COMMISSION,
    COMPTE_ESCROW,
    COMPTE_EXTERNE,
)
from tests.conftest import (
    assigner_transporteur,
    confirmer_reception,
    creer_offre,
    creer_transporteur_valide,
    creer_utilisateur,
    payer_commande,
)


def _commande_prete(client, produit_id, prix=500, qte=2):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=100, prix=prix)
    ach = creer_utilisateur(client, "ACHETEUR")
    cmd = client.post(
        "/api/v1/commandes",
        headers=ach["headers"],
        json={"lignes": [{"offre_id": offre["id"], "quantite": qte}]},
    ).json()
    return prod, ach, cmd


def _transition(client, headers, cid, action):
    return client.post(
        f"/api/v1/commandes/{cid}/transition", headers=headers, json={"action": action}
    )


def test_paiement_sequestre_ledger(client, produit_id, db_session):
    prod, ach, cmd = _commande_prete(client, produit_id)  # 2 * 500 = 1000
    escrow = payer_commande(client, ach["headers"], cmd["id"])
    assert escrow["statut"] == "SEQUESTRE"
    assert escrow["montant"] == 1000

    statut = client.get(f"/api/v1/commandes/{cmd['id']}", headers=ach["headers"]).json()["statut"]
    assert statut == "PAYEE_SEQUESTRE"

    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 1000
    assert ledger_service.solde(db_session, COMPTE_EXTERNE) == -1000
    assert ledger_service.solde_global(db_session) == 0


def test_cycle_complet_liberation(client, produit_id, db_session):
    prod, ach, cmd = _commande_prete(client, produit_id)  # 1000
    cid = cmd["id"]
    payer_commande(client, ach["headers"], cid)
    _transition(client, prod["headers"], cid, "PREPARER")
    transp = creer_transporteur_valide(client, db_session)
    code = assigner_transporteur(client, prod["headers"], cid, transp["transporteur_id"])
    _transition(client, prod["headers"], cid, "EXPEDIER")
    r = confirmer_reception(client, ach["headers"], cid, code)
    assert r.status_code == 200 and r.json()["statut"] == "FONDS_LIBERES"

    esc = client.get(f"/api/v1/commandes/{cid}/escrow", headers=ach["headers"]).json()
    assert esc["statut"] == "LIBERE"
    assert esc["commission"] == 50  # 5% de 1000
    assert esc["montant_net"] == 950

    compte_prod = f"PRODUCTEUR:{prod['user']['id']}"
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 0
    assert ledger_service.solde(db_session, COMPTE_COMMISSION) == 50
    assert ledger_service.solde(db_session, compte_prod) == 0  # payé puis soldé
    assert ledger_service.solde(db_session, COMPTE_EXTERNE) == -50
    # Invariant clé : le solde ne fuit jamais.
    assert ledger_service.solde_global(db_session) == 0


def test_double_paiement_idempotent(client, produit_id, db_session):
    prod, ach, cmd = _commande_prete(client, produit_id)
    e1 = payer_commande(client, ach["headers"], cmd["id"])
    e2 = payer_commande(client, ach["headers"], cmd["id"])
    assert e1["id"] == e2["id"]
    # Le dépôt n'est passé qu'une fois.
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 1000
    assert ledger_service.solde_global(db_session) == 0


def test_double_webhook_idempotent(client, produit_id, db_session):
    prod, ach, cmd = _commande_prete(client, produit_id)
    payer_commande(client, ach["headers"], cmd["id"])  # déjà confirmé (sandbox)

    # Rejoue le MÊME webhook de confirmation.
    event = SandboxProvider().construire_evenement_depot(
        ref_transaction="sbx-rejoue", montant=1000, idempotency_key=f"depot:{cmd['id']}"
    )
    r = client.post("/api/v1/webhooks/paiement", json=event)
    assert r.status_code == 200
    # Toujours un seul dépôt séquestré.
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 1000
    assert ledger_service.solde_global(db_session) == 0


def test_signature_invalide_rejetee(client):
    event = {
        "type": "depot.confirme",
        "ref_transaction": "x",
        "idempotency_key": "depot:inexistant",
        "montant": 1000,
        "signature": "deadbeef",
    }
    r = client.post("/api/v1/webhooks/paiement", json=event)
    assert r.status_code == 401


def test_double_validation_montant(client, produit_id, db_session):
    """Un webhook signé mais au mauvais montant est rejeté (double validation)."""
    prod, ach, cmd = _commande_prete(client, produit_id)  # montant 1000
    cid = uuid.UUID(cmd["id"])
    # Crée un séquestre EN_ATTENTE sans passer par le sandbox auto-confirmant.
    escrow = EscrowTransaction(
        commande_id=cid,
        montant=1000,
        statut=EscrowStatut.EN_ATTENTE,
        idempotency_key=f"depot:{cid}",
        ref_depot="manuel",
    )
    db_session.add(escrow)
    db_session.commit()

    # Webhook signé mais montant falsifié (1 au lieu de 1000).
    event = SandboxProvider().construire_evenement_depot(
        ref_transaction="x", montant=1, idempotency_key=f"depot:{cid}"
    )
    try:
        escrow_service.traiter_webhook(db_session, event)
        assert False, "aurait dû lever EscrowError"
    except escrow_service.EscrowError as exc:
        assert exc.status_code == 422

    db_session.refresh(escrow)
    assert escrow.statut == EscrowStatut.EN_ATTENTE  # inchangé
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 0


def test_seul_acheteur_paie(client, produit_id):
    prod, ach, cmd = _commande_prete(client, produit_id)
    # Le producteur (qui voit la commande) ne peut pas la payer.
    r = client.post(f"/api/v1/commandes/{cmd['id']}/payer", headers=prod["headers"])
    assert r.status_code == 403
