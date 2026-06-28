"""Tests des commandes : création atomique, montant serveur, stock, visibilité."""
from tests.conftest import creer_offre, creer_utilisateur


def _commander(client, headers, offre_id, quantite):
    return client.post(
        "/api/v1/commandes",
        headers=headers,
        json={"lignes": [{"offre_id": offre_id, "quantite": quantite}]},
    )


def test_creation_commande_montant_et_stock(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=100, prix=500)
    ach = creer_utilisateur(client, "ACHETEUR")

    resp = _commander(client, ach["headers"], offre["id"], 10)
    assert resp.status_code == 201, resp.text
    cmd = resp.json()
    # Montant recalculé serveur : 10 * 500 = 5000 FCFA
    assert cmd["montant_total"] == 5000
    assert cmd["statut"] == "CREEE"
    assert cmd["producteur_id"] == prod["user"]["id"]

    # Stock décrémenté côté serveur.
    detail = client.get(f"/api/v1/offres/{offre['id']}", headers=ach["headers"]).json()
    assert detail["quantite_disponible"] == 90


def test_montant_client_ignore(client, produit_id):
    """Même si le client envoie un prix, le serveur recalcule depuis la base."""
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=100, prix=500)
    ach = creer_utilisateur(client, "ACHETEUR")
    resp = client.post(
        "/api/v1/commandes",
        headers=ach["headers"],
        json={
            "lignes": [{"offre_id": offre["id"], "quantite": 2}],
            "montant_total": 1,  # tentative d'injection — doit être ignorée
            "prix_unitaire": 1,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["montant_total"] == 1000


def test_stock_insuffisant_refuse(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=5)
    ach = creer_utilisateur(client, "ACHETEUR")
    resp = _commander(client, ach["headers"], offre["id"], 10)
    assert resp.status_code == 409
    # Stock inchangé (rollback atomique).
    detail = client.get(f"/api/v1/offres/{offre['id']}", headers=prod["headers"]).json()
    assert detail["quantite_disponible"] == 5


def test_commande_multi_producteur_refusee(client, produit_id):
    prod1 = creer_utilisateur(client, "PRODUCTEUR")
    prod2 = creer_utilisateur(client, "PRODUCTEUR")
    o1 = creer_offre(client, prod1["headers"], produit_id)
    o2 = creer_offre(client, prod2["headers"], produit_id)
    ach = creer_utilisateur(client, "ACHETEUR")
    resp = client.post(
        "/api/v1/commandes",
        headers=ach["headers"],
        json={
            "lignes": [
                {"offre_id": o1["id"], "quantite": 1},
                {"offre_id": o2["id"], "quantite": 1},
            ]
        },
    )
    assert resp.status_code == 422


def test_producteur_ne_peut_pas_commander(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id)
    resp = _commander(client, prod["headers"], offre["id"], 1)
    assert resp.status_code == 403


def test_epuisement_passe_offre_en_epuisee(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=10)
    ach = creer_utilisateur(client, "ACHETEUR")
    assert _commander(client, ach["headers"], offre["id"], 10).status_code == 201
    detail = client.get(f"/api/v1/offres/{offre['id']}", headers=prod["headers"]).json()
    assert detail["quantite_disponible"] == 0
    assert detail["statut"] == "EPUISEE"


def test_visibilite_commande(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id)
    ach = creer_utilisateur(client, "ACHETEUR")
    autre = creer_utilisateur(client, "ACHETEUR")
    cmd = _commander(client, ach["headers"], offre["id"], 1).json()

    # Le producteur concerné voit la commande.
    assert client.get(f"/api/v1/commandes/{cmd['id']}", headers=prod["headers"]).status_code == 200
    # Un autre acheteur ne la voit pas.
    assert client.get(f"/api/v1/commandes/{cmd['id']}", headers=autre["headers"]).status_code == 403


def test_mes_commandes_par_role(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id)
    ach = creer_utilisateur(client, "ACHETEUR")
    _commander(client, ach["headers"], offre["id"], 1)
    assert len(client.get("/api/v1/commandes/mes", headers=ach["headers"]).json()) == 1
    assert len(client.get("/api/v1/commandes/mes", headers=prod["headers"]).json()) == 1
