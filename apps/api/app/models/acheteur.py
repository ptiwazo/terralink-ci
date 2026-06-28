"""Table `acheteurs` — profil acheteur + plafond de crédit (CLAUDE.md §4)."""
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
from app.models.enums import AcheteurType


class Acheteur(Base):
    __tablename__ = "acheteurs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    type: Mapped[AcheteurType] = mapped_column(
        SAEnum(AcheteurType, native_enum=False, length=20), nullable=False
    )
    adresse: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Plafond accordé manuellement (OPS). Le plafond effectif combine ce montant
    # avec le scoring basé sur l'historique (cf. acheteur_service.eligibilite).
    plafond_credit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
