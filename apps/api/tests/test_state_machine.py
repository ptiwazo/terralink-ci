"""Tests de la machine à états des commandes (CLAUDE.md §5).

Depuis la Phase 2, le passage à PAYEE_SEQUESTRE se fait via l'escrow (paiement),
et CONFIRMER_RECEPTION libère les fonds → la commande termine en FONDS_LIBERES.
"""
from tests.conftest import (
    creer_interne,
    creer_offre,
    creer_utilisateur,
    payer_commande,
)


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


def test_parcours_complet_jusqua_fonds_liberes(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    cid = cmd["id"]

    payer_commande(client, ach["headers"], cid)
    statut = client.get(f"/api/v1/commandes/{cid}", headers=ach["headers"]).json()["statut"]
    assert statut == "PAYEE_SEQUESTRE"

    r = _transition(client, prod["headers"], cid, "PREPARER")
    assert r.status_code == 200 and r.json()["statut"] == "EN_PREPARATION"

    r = _transition(client, prod["headers"], cid, "EXPEDIER")
    assert r.status_code == 200 and r.json()["statut"] == "EN_LIVRAISON"

    r = _transition(client, ach["headers"], cid, "CONFIRMER_RECEPTION")
    assert r.status_code == 200 and r.json()["statut"] == "FONDS_LIBERES"


def test_preparer_par_acheteur_refuse(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    payer_commande(client, ach["headers"], cmd["id"])
    # PREPARER exige le rôle producteur.
    r = _transition(client, ach["headers"], cmd["id"], "PREPARER")
    assert r.status_code == 403


def test_transition_illegale_depuis_creee(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    # PREPARER impossible depuis CREEE (commande non payée).
    r = _transition(client, prod["headers"], cmd["id"], "PREPARER")
    assert r.status_code == 409


def test_proprietaire_requis(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    payer_commande(client, ach["headers"], cmd["id"])
    autre_prod = creer_utilisateur(client, "PRODUCTEUR")
    # Bon rôle (PRODUCTEUR) mais pas LE producteur de la commande.
    r = _transition(client, autre_prod["headers"], cmd["id"], "PREPARER")
    assert r.status_code == 403


def test_action_inconnue(client, produit_id):
    prod, ach, cmd = _setup_commande(client, produit_id)
    r = _transition(client, ach["headers"], cmd["id"], "FONDS_LIBERES")
    assert r.status_code == 400


def test_paiement_manuel_impossible(client, produit_id):
    """On ne peut PAS sauter à PAYEE_SEQUESTRE par une transition manuelle."""
    prod, ach, cmd = _setup_commande(client, produit_id)
    r = _transition(client, ach["headers"], cmd["id"], "SIMULER_PAIEMENT")
    assert r.status_code == 400  # action retirée de la machine à états


def test_ops_peut_agir_sur_toute_commande(client, produit_id, db_session):
    prod, ach, cmd = _setup_commande(client, produit_id)
    payer_commande(client, ach["headers"], cmd["id"])
    ops = creer_interne(db_session, "OPS")
    r = _transition(client, ops["headers"], cmd["id"], "PREPARER")
    assert r.status_code == 200 and r.json()["statut"] == "EN_PREPARATION"
