"""Tests du contrôle d'accès par rôle (CLAUDE.md §2.2)."""
from fastapi import Depends

from app.core.deps import require_roles
from app.main import app
from app.models.enums import Role
from tests.conftest import register_payload


# Route temporaire montée pour tester require_roles de façon isolée.
@app.get("/api/v1/_test/admin-only")
def _admin_only(_user=Depends(require_roles(Role.ADMIN))) -> dict:
    return {"ok": True}


def _token_for(client, role: str, telephone: str) -> str:
    payload = register_payload(role=role, telephone=telephone)
    return client.post("/api/v1/auth/register", json=payload).json()["tokens"][
        "access_token"
    ]


def test_dashboard_sections_par_role(client):
    token = _token_for(client, "ACHETEUR", "+2250700000010")
    resp = client.get(
        "/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "ACHETEUR"
    assert "Catalogue" in body["sections"]


def test_role_non_autorise_rejete(client):
    """Un PRODUCTEUR ne doit pas accéder à une route réservée ADMIN."""
    token = _token_for(client, "PRODUCTEUR", "+2250700000011")
    resp = client.get(
        "/api/v1/_test/admin-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_sans_token_rejete(client):
    resp = client.get("/api/v1/_test/admin-only")
    assert resp.status_code in (401, 403)
