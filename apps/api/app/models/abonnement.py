"""Table `abonnements_premium` (CLAUDE.md §4)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import AbonnementFormule, AbonnementStatut


class AbonnementPremium(Base):
    __tablename__ = "abonnements_premium"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    acheteur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    formule: Mapped[AbonnementFormule] = mapped_column(
        SAEnum(AbonnementFormule, native_enum=False, length=20), nullable=False
    )
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prix: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    statut: Mapped[AbonnementStatut] = mapped_column(
        SAEnum(AbonnementStatut, native_enum=False, length=20),
        nullable=False,
        default=AbonnementStatut.ACTIF,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
