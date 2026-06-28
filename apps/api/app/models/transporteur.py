"""Table `transporteurs` — profil + caution + validation (CLAUDE.md §4)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import TransporteurStatut


class Transporteur(Base):
    __tablename__ = "transporteurs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    vehicule: Mapped[str] = mapped_column(String(120), nullable=False)
    immatriculation: Mapped[str] = mapped_column(String(40), nullable=False)
    caution_deposee: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    statut: Mapped[TransporteurStatut] = mapped_column(
        SAEnum(TransporteurStatut, native_enum=False, length=20),
        nullable=False,
        default=TransporteurStatut.EN_ATTENTE,
        index=True,
    )
    note: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
