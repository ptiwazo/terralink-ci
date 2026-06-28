"""Fixtures de test.

Stratégie : on cible une base PostgreSQL de test (TEST_DATABASE_URL),
on crée le schéma une fois, et chaque test s'exécute dans une transaction
annulée (rollback) à la fin — isolation totale entre tests.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db
from app.main import app
from app.models import Base
from app.models.enums import Unite
from app.models.produit import Produit

engine = create_engine(settings.test_database_url, pool_pre_ping=True, future=True)

# Produits de référence semés une fois pour la session de test.
SEED_PRODUITS = [
    ("Manioc", "Tubercules", Unite.KG),
    ("Banane plantain", "Fruits", Unite.REGIME),
    ("Tomate", "Légumes", Unite.KG),
]


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """Recrée le schéma propre + seed produits pour la session de test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as s:
        for nom, cat, unite in SEED_PRODUITS:
            s.add(Produit(id=uuid.uuid4(), nom=nom, categorie=cat, unite=unite, actif=True))
        s.commit()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Session encapsulée dans une transaction annulée après chaque test.

    On « rejoint » une transaction externe : la session ouvre un SAVEPOINT
    (`join_transaction_mode="create_savepoint"`), si bien que les `db.commit()`
    du service ne valident qu'un savepoint. Le `rollback()` de la transaction
    externe annule tout — isolation parfaite entre tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """TestClient FastAPI partageant la session transactionnelle du test."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_payload(**overrides) -> dict:
    base = {
        "telephone": "+2250700000001",
        "nom": "Awa Koné",
        "mot_de_passe": "motdepasse123",
        "role": "PRODUCTEUR",
    }
    base.update(overrides)
    return base


@pytest.fixture
def produit_id(db_session) -> str:
    """Id d'un produit de référence semé."""
    p = db_session.scalar(select(Produit).where(Produit.nom == "Manioc"))
    return str(p.id)


_compteur_tel = [600000]


def creer_utilisateur(client, role: str, nom: str = "Utilisateur Test") -> dict:
    """Inscrit un utilisateur d'un rôle donné et renvoie token + headers + user."""
    _compteur_tel[0] += 1
    tel = f"+225070{_compteur_tel[0]}"
    resp = client.post(
        "/api/v1/auth/register",
        json={"telephone": tel, "nom": nom, "mot_de_passe": "motdepasse123", "role": role},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    token = body["tokens"]["access_token"]
    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user": body["user"],
    }


def payer_commande(client, acheteur_headers: dict, commande_id: str) -> dict:
    """Paie une commande via l'escrow (le sandbox confirme automatiquement le
    dépôt). Renvoie l'escrow."""
    resp = client.post(
        f"/api/v1/commandes/{commande_id}/payer", headers=acheteur_headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def creer_interne(db_session, role: str, nom: str = "Agent Interne") -> dict:
    """Crée un utilisateur OPS/ADMIN directement en base (non inscriptible via API)
    et forge un token d'accès valide."""
    from app.core.security import create_access_token, hash_password
    from app.models.enums import Role, UserStatus
    from app.models.user import User

    _compteur_tel[0] += 1
    user = User(
        id=uuid.uuid4(),
        telephone=f"+225050{_compteur_tel[0]}",
        nom=nom,
        mot_de_passe_hash=hash_password("motdepasse123"),
        role=Role(role),
        statut=UserStatus.ACTIF,
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(str(user.id))
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}, "user": user}


def creer_offre(
    client,
    producteur_headers: dict,
    produit_id: str,
    *,
    quantite: int = 100,
    prix: int = 500,
    qualite: str = "Premier choix",
    dispo_le: str = "2026-07-15",
    lat: float | None = 5.345,
    lng: float | None = -4.024,
) -> dict:
    resp = client.post(
        "/api/v1/offres",
        headers=producteur_headers,
        json={
            "produit_id": produit_id,
            "quantite_disponible": quantite,
            "prix_unitaire": prix,
            "qualite": qualite,
            "dispo_le": dispo_le,
            "lat": lat,
            "lng": lng,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
