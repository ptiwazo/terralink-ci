"""Tests de la machine à états des commandes (CLAUDE.md §5)."""
from tests.conftest import creer_interne, creer_offre, creer_utilisateur


def _setup_commande(client, produit_id):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    offre = creer_offre(client, prod["headers"], produit_id, quantite=100, prix=500)
    ach = creer_utilisateur(client, "ACHETEUR")
    cmd = client.post(
        "/api/v1/commandes",
        headers=ach["headers"],
        json={"lignes": [{"offre_id": offre["id"], "quantite": 2}]},
    ).json()
    return prod, ach, cmd


def _transition(client, headers, commande_id, action):
    return client.post(
        f"/api/v1/commandes/{commande_id}/transition",
        headers=headers,
        json={"action": action},
    )


def test_parcours_complet_jusqua_livree(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    cid = cmd["id"]

    r = _transition(client, ach["headers"], cid, "SIMULER_PAIEMENT")
    assert r.status_code == 200 and r.json()["statut"] == "PAYEE_SEQUESTRE"

    r = _transition(client, prod["headers"], cid, "PREPARER")
    assert r.status_code == 200 and r.json()["statut"] == "EN_PREPARATION"

    r = _transition(client, prod["headers"], cid, "EXPEDIER")
    assert r.status_code == 200 and r.json()["statut"] == "EN_LIVRAISON"

    r = _transition(client, ach["headers"], cid, "CONFIRMER_RECEPTION")
    assert r.status_code == 200 and r.json()["statut"] == "LIVREE_CONFORME"


def test_mauvais_role_refuse(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    # Le producteur ne peut pas déclencher le paiement (rôle acheteur requis).
    r = _transition(client, prod["headers"], cmd["id"], "SIMULER_PAIEMENT")
    assert r.status_code == 403


def test_transition_illegale_depuis_creee(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    # PREPARER n'est possible que depuis PAYEE_SEQUESTRE, pas depuis CREEE.
    r = _transition(client, prod["headers"], cmd["id"], "PREPARER")
    assert r.status_code == 409


def test_proprietaire_requis(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    cid = cmd["id"]
    _transition(client, ach["headers"], cid, "SIMULER_PAIEMENT")
    # Un autre producteur a bien le rôle PRODUCTEUR mais n'est pas CE producteur.
    autre_prod = creer_utilisateur(client, "PRODUCTEUR")
    r = _transition(client, autre_prod["headers"], cid, "PREPARER")
    assert r.status_code == 403


def test_action_inconnue(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    r = _transition(client, ach["headers"], cmd["id"], "FONDS_LIBERES")
    assert r.status_code == 400


def test_ops_peut_agir_sur_toute_commande(client, produit_id, db_session):
    prod, ach, cmd = _setup_commande(client, produit_id)
    cid = cmd["id"]
    _transition(client, ach["headers"], cid, "SIMULER_PAIEMENT")
    ops = creer_interne(db_session, "OPS")
    # OPS n'est ni l'acheteur ni le producteur, mais rôle interne autorisé.
    r = _transition(client, ops["headers"], cid, "PREPARER")
    assert r.status_code == 200 and r.json()["statut"] == "EN_PREPARATION"
