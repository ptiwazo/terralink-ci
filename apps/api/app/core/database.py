"""Moteur SQLAlchemy et fabrique de sessions.

On utilise SQLAlchemy 2.0 en mode synchrone : les transactions atomiques
(essentielles au cœur financier, cf. CLAUDE.md §2.1) sont explicites et
simples à raisonner avec `with session.begin()`.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
    expire_on_commit=False,
)
