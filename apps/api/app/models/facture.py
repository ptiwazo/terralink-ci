"""Tables `factures` et `facture_sequences` (CLAUDE.md §2.3, §4).

Numérotation OHADA : **suite continue, sans trou, par exercice**. Le compteur
`facture_sequences` est incrémenté sous verrou (FOR UPDATE) dans la MÊME
transaction que la création de la facture — un rollback annule les deux, donc
aucun numéro n'est jamais sauté.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FactureSequence(Base):
    """Compteur de numérotation par exercice (année)."""

    __tablename__ = "facture_sequences"

    exercice: Mapped[int] = mapped_column(Integer, primary_key=True)
    dernier_numero: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Facture(Base):
    __tablename__ = "factures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    numero: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    exercice: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    commande_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commandes.id"), nullable=False, unique=True
    )
    montant_ht: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tva: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    montant_ttc: Mapped[int] = mapped_column(BigInteger, nullable=False)
    pdf_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
