"""Table `escrow_transactions` — un séquestre par commande (CLAUDE.md §4)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import EscrowStatut


class EscrowTransaction(Base):
    __tablename__ = "escrow_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    commande_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commandes.id"), nullable=False, unique=True
    )
    montant: Mapped[int] = mapped_column(BigInteger, nullable=False)  # FCFA séquestrés
    commission: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    montant_net: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    statut: Mapped[EscrowStatut] = mapped_column(
        SAEnum(EscrowStatut, native_enum=False, length=20),
        nullable=False,
        default=EscrowStatut.EN_ATTENTE,
        index=True,
    )
    # Clé d'idempotence du dépôt + références fournisseur de paiement.
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    ref_depot: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ref_paiement: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
