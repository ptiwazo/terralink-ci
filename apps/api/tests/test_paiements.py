"""Tests de la section « Mes paiements » (producteur)."""
from tests.conftest import creer_utilisateur, livrer_comptant


def test_mes_paiements_escrow(client, produit_id, db_session):
    # Commande comptant livrée : 3 × 1000 = 3000, commission 5% = 150 -> net 2850.
    res = livrer_comptant(client, db_session, produit_id, prix=1000, qte=3)
    r = client.get("/api/v1/paiements/mes", headers=res["prod"]["headers"])
    assert r.status_code == 200
    data = r.json()
    assert data["nb"] == 1
    assert data["total_recu"] == 2850
    p = data["paiements"][0]
    assert p["type"] == "ESCROW"
    assert p["montant"] == 2850
    assert p["statut"] == "VERSE"


def test_mes_paiements_reserve_au_producteur(client):
    ach = creer_utilisateur(client, "ACHETEUR")
    assert client.get("/api/v1/paiements/mes", headers=ach["headers"]).status_code == 403
