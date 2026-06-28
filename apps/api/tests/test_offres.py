"""Tests des offres (CRUD producteur + contrôle de propriété)."""
from tests.conftest import creer_offre, creer_utilisateur


def test_producteur_cree_offre(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=50, prix=750)
    assert offre["statut"] == "DISPONIBLE"
    assert offre["prix_unitaire"] == 750
    assert offre["quantite_disponible"] == 50
    assert offre["produit"]["nom"] == "Manioc"
    assert offre["producteur"]["id"] == prod["user"]["id"]


def test_acheteur_ne_peut_pas_creer_offre(client, produit_id):
    ach = creer_utilisateur(client, "ACHETEUR")
    resp = client.post(
        "/api/v1/offres",
        headers=ach["headers"],
        json={
            "produit_id": produit_id,
            "quantite_disponible": 10,
            "prix_unitaire": 100,
            "dispo_le": "2026-07-15",
        },
    )
    assert resp.status_code == 403


def test_prix_negatif_refuse(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    resp = client.post(
        "/api/v1/offres",
        headers=prod["headers"],
        json={
            "produit_id": produit_id,
            "quantite_disponible": 10,
            "prix_unitaire": -5,
            "dispo_le": "2026-07-15",
        },
    )
    assert resp.status_code == 422


def test_lister_mes_offres(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    creer_offre(client, prod["headers"], produit_id)
    creer_offre(client, prod["headers"], produit_id, prix=900)
    resp = client.get("/api/v1/offres/mes", headers=prod["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_maj_offre_par_proprietaire(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, prix=500)
    resp = client.patch(
        f"/api/v1/offres/{offre['id']}",
        headers=prod["headers"],
        json={"prix_unitaire": 650},
    )
    assert resp.status_code == 200
    assert resp.json()["prix_unitaire"] == 650


def test_maj_offre_autre_producteur_refuse(client, produit_id):
    prod1 = creer_utilisateur(client, "PRODUCTEUR")
    prod2 = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod1["headers"], produit_id)
    resp = client.patch(
        f"/api/v1/offres/{offre['id']}",
        headers=prod2["headers"],
        json={"prix_unitaire": 1},
    )
    assert resp.status_code == 403


def test_retrait_offre(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id)
    resp = client.delete(f"/api/v1/offres/{offre['id']}", headers=prod["headers"])
    assert resp.status_code == 200
    assert resp.json()["statut"] == "RETIREE"
