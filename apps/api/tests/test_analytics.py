"""Tests prévisions de récolte et KPIs (Phase 5)."""
from tests.conftest import (
    creer_interne,
    creer_offre,
    creer_utilisateur,
    livrer_comptant,
)


def test_previsions_recolte(client, produit_id, db_session):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    creer_offre(client, prod["headers"], produit_id, quantite=100, dispo_le="2026-12-01")
    creer_offre(client, prod["headers"], produit_id, quantite=50, dispo_le="2026-11-01")
    ach = creer_utilisateur(client, "ACHETEUR")
    prevs = client.get("/api/v1/previsions", headers=ach["headers"]).json()
    manioc = next((p for p in prevs if p["produit"] == "Manioc"), None)
    assert manioc is not None
    assert manioc["quantite_totale"] >= 150
    assert manioc["nb_offres"] >= 2


def test_kpis(client, produit_id, db_session):
    res = livrer_comptant(client, db_session, produit_id, prix=1000, qte=2)  # 2000, livrée
    ops = creer_interne(db_session, "OPS")
    k = client.get("/api/v1/kpis", headers=ops["headers"]).json()
    assert k["nb_commandes"] >= 1
    assert k["gmv"] >= 2000
    assert "par_statut" in k and "revenus" in k
    # La commande livrée a généré une commission (5% de 2000 = 100).
    assert k["revenus"]["commission"] >= 100


def test_kpis_reserve_aux_ops(client, produit_id):
    ach = creer_utilisateur(client, "ACHETEUR")
    r = client.get("/api/v1/kpis", headers=ach["headers"])
    assert r.status_code == 403
