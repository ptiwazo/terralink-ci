"""Tests de la recherche catalogue (produit, proximité, délai)."""
from tests.conftest import creer_offre, creer_utilisateur


def test_recherche_par_produit(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    creer_offre(client, prod["headers"], produit_id)
    ach = creer_utilisateur(client, "ACHETEUR")
    resp = client.get(
        "/api/v1/catalogue", headers=ach["headers"], params={"produit_id": produit_id}
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["offre"]["produit"]["id"] == produit_id


def test_filtre_proximite(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    # Abidjan (proche) et Korhogo (loin, ~500 km)
    creer_offre(client, prod["headers"], produit_id, lat=5.345, lng=-4.024, prix=100)
    creer_offre(client, prod["headers"], produit_id, lat=9.458, lng=-5.629, prix=200)
    ach = creer_utilisateur(client, "ACHETEUR")
    resp = client.get(
        "/api/v1/catalogue",
        headers=ach["headers"],
        params={"lat": 5.345, "lng": -4.024, "rayon_km": 50},
    )
    assert resp.status_code == 200
    items = resp.json()
    # Seule l'offre d'Abidjan est dans le rayon de 50 km.
    assert len(items) == 1
    assert items[0]["distance_km"] < 50


def test_tri_par_distance(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    creer_offre(client, prod["headers"], produit_id, lat=9.458, lng=-5.629)  # loin
    creer_offre(client, prod["headers"], produit_id, lat=5.345, lng=-4.024)  # proche
    ach = creer_utilisateur(client, "ACHETEUR")
    resp = client.get(
        "/api/v1/catalogue",
        headers=ach["headers"],
        params={"lat": 5.345, "lng": -4.024},
    )
    items = resp.json()
    assert len(items) == 2
    assert items[0]["distance_km"] <= items[1]["distance_km"]


def test_offre_retiree_absente_du_catalogue(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id)
    client.delete(f"/api/v1/offres/{offre['id']}", headers=prod["headers"])
    ach = creer_utilisateur(client, "ACHETEUR")
    resp = client.get(
        "/api/v1/catalogue", headers=ach["headers"], params={"produit_id": produit_id}
    )
    ids = [i["offre"]["id"] for i in resp.json()]
    assert offre["id"] not in ids
