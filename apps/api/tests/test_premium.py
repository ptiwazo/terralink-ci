"""Tests des abonnements premium (Phase 5)."""
from app.services import ledger_service
from app.services.ledger_service import COMPTE_ABONNEMENT
from tests.conftest import creer_utilisateur


def test_souscription_premium(client, db_session):
    ach = creer_utilisateur(client, "ACHETEUR")
    r = client.post("/api/v1/premium/souscrire", headers=ach["headers"], json={"formule": "PREMIUM"})
    assert r.status_code == 200, r.text
    abo = r.json()
    assert abo["statut"] == "ACTIF"
    assert abo["prix"] == 25000
    # Revenu d'abonnement comptabilisé, solde global préservé.
    assert ledger_service.solde(db_session, COMPTE_ABONNEMENT) == 25000
    assert ledger_service.solde_global(db_session) == 0


def test_mon_abonnement(client):
    ach = creer_utilisateur(client, "ACHETEUR")
    client.post("/api/v1/premium/souscrire", headers=ach["headers"], json={"formule": "PREMIUM"})
    r = client.get("/api/v1/premium/mon-abonnement", headers=ach["headers"])
    assert r.status_code == 200 and r.json()["formule"] == "PREMIUM"


def test_souscription_idempotente(client):
    ach = creer_utilisateur(client, "ACHETEUR")
    a1 = client.post("/api/v1/premium/souscrire", headers=ach["headers"], json={"formule": "PREMIUM"}).json()
    a2 = client.post("/api/v1/premium/souscrire", headers=ach["headers"], json={"formule": "PREMIUM"}).json()
    assert a1["id"] == a2["id"]  # période active réutilisée


def test_non_acheteur_refuse(client):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    r = client.post("/api/v1/premium/souscrire", headers=prod["headers"], json={"formule": "PREMIUM"})
    assert r.status_code == 403
