"""Fixtures de test.

Stratégie : on cible une base PostgreSQL de test (TEST_DATABASE_URL),
on crée le schéma une fois, et chaque test s'exécute dans une transaction
annulée (rollback) à la fin — isolation totale entre tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db
from app.main import app
from app.models import Base

engine = create_engine(settings.test_database_url, pool_pre_ping=True, future=True)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """Recrée le schéma propre pour la session de test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
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
