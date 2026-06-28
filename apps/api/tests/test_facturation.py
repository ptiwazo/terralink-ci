"""Tests de la facturation OHADA (CLAUDE.md §2.3, Phase 5).

Garantie clé : numérotation séquentielle, continue, **sans trou**, par exercice.
"""
import os
from datetime import datetime, timezone

from tests.conftest import creer_interne, creer_utilisateur, livrer_comptant


def _emettre(client, ops_headers, cid):
    return client.post(f"/api/v1/commandes/{cid}/facture", headers=ops_headers)


def test_emission_facture(client, produit_id, db_session):
    res = livrer_comptant(client, db_session, produit_id, prix=1000, qte=3)  # 3000
    ops = creer_interne(db_session, "OPS")
    r = _emettre(client, ops["headers"], res["cid"])
    assert r.status_code == 200, r.text
    f = r.json()
    assert f["exercice"] == datetime.now(timezone.utc).year
    assert f["numero"] == f"{f['exercice']}-0000001"
    assert f["montant_ht"] == 3000
    assert f["montant_ttc"] == 3000  # TVA 0 par défaut
    assert f["pdf_ref"] and os.path.exists(f["pdf_ref"])


def test_numerotation_sequentielle_sans_trou(client, produit_id, db_session):
    ops = creer_interne(db_session, "OPS")
    numeros = []
    for _ in range(3):
        res = livrer_comptant(client, db_session, produit_id)
        numeros.append(_emettre(client, ops["headers"], res["cid"]).json()["sequence"])
    # Séquences strictement consécutives.
    assert numeros == sorted(numeros)
    for a, b in zip(numeros, numeros[1:]):
        assert b == a + 1


def test_emission_idempotente(client, produit_id, db_session):
    res = livrer_comptant(client, db_session, produit_id)
    ops = creer_interne(db_session, "OPS")
    f1 = _emettre(client, ops["headers"], res["cid"]).json()
    f2 = _emettre(client, ops["headers"], res["cid"]).json()
    assert f1["numero"] == f2["numero"]  # pas de second numéro consommé


def test_commande_non_facturable_refusee(client, produit_id, db_session):
    prod = creer_utilisateur(client, "PRODUCTEUR")
    ach = creer_utilisateur(client, "ACHETEUR")
    from tests.conftest import creer_offre

    offre = creer_offre(client, prod["headers"], produit_id)
    cmd = client.post(
        "/api/v1/commandes",
        headers=ach["headers"],
        json={"lignes": [{"offre_id": offre["id"], "quantite": 1}]},
    ).json()
    ops = creer_interne(db_session, "OPS")
    r = _emettre(client, ops["headers"], cmd["id"])  # encore CREEE
    assert r.status_code == 409


def test_facturation_reservee_aux_ops(client, produit_id, db_session):
    res = livrer_comptant(client, db_session, produit_id)
    r = _emettre(client, res["ach"]["headers"], res["cid"])
    assert r.status_code == 403


def test_telechargement_pdf(client, produit_id, db_session):
    res = livrer_comptant(client, db_session, produit_id)
    ops = creer_interne(db_session, "OPS")
    _emettre(client, ops["headers"], res["cid"])
    r = client.get(f"/api/v1/factures/{res['cid']}/pdf", headers=res["ach"]["headers"])
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
