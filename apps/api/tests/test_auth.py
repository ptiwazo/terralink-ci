"""Tests du parcours d'authentification (Phase 0)."""
from tests.conftest import register_payload


def test_register_ok(client):
    resp = client.post("/api/v1/auth/register", json=register_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["telephone"] == "+2250700000001"
    assert body["user"]["role"] == "PRODUCTEUR"
    assert "mot_de_passe_hash" not in body["user"]  # jamais exposé
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]


def test_register_telephone_duplique(client):
    client.post("/api/v1/auth/register", json=register_payload())
    resp = client.post("/api/v1/auth/register", json=register_payload(nom="Autre"))
    assert resp.status_code == 409


def test_register_role_admin_refuse(client):
    resp = client.post("/api/v1/auth/register", json=register_payload(role="ADMIN"))
    assert resp.status_code == 422  # validé par Pydantic


def test_register_mot_de_passe_trop_court(client):
    resp = client.post(
        "/api/v1/auth/register", json=register_payload(mot_de_passe="court")
    )
    assert resp.status_code == 422


def test_login_ok(client):
    client.post("/api/v1/auth/register", json=register_payload())
    resp = client.post(
        "/api/v1/auth/login",
        json={"telephone": "+2250700000001", "mot_de_passe": "motdepasse123"},
    )
    assert resp.status_code == 200
    assert resp.json()["tokens"]["access_token"]


def test_login_mauvais_mot_de_passe(client):
    client.post("/api/v1/auth/register", json=register_payload())
    resp = client.post(
        "/api/v1/auth/login",
        json={"telephone": "+2250700000001", "mot_de_passe": "faux-mot-de-passe"},
    )
    assert resp.status_code == 401


def test_me_requiert_token(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code in (401, 403)


def test_me_avec_token(client):
    reg = client.post("/api/v1/auth/register", json=register_payload()).json()
    token = reg["tokens"]["access_token"]
    resp = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["telephone"] == "+2250700000001"


def test_refresh_renouvelle_access(client):
    reg = client.post("/api/v1/auth/register", json=register_payload()).json()
    refresh = reg["tokens"]["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_refresh_avec_access_token_refuse(client):
    """Un access token ne doit pas pouvoir servir de refresh token."""
    reg = client.post("/api/v1/auth/register", json=register_payload()).json()
    access = reg["tokens"]["access_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401
