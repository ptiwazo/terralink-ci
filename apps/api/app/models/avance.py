"""Table `avances_tresorerie` — une avance par commande différée (CLAUDE.md §4).

`montant` = créance due par l'acheteur (= montant_total de la commande).
`montant_avance` = versé au producteur (= montant − commission − décote).
Montants en entiers FCFA.
"""
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
from app.models.enums import AvanceStatut


class AvanceTresorerie(Base):
    __tablename__ = "avances_tresorerie"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    commande_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commandes.id"), nullable=False, unique=True
    )
    acheteur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    montant: Mapped[int] = mapped_column(BigInteger, nullable=False)  # créance FCFA
    montant_avance: Mapped[int] = mapped_column(BigInteger, nullable=False)
    commission: Mapped[int] = mapped_column(BigInteger, nullable=False)
    decote: Mapped[int] = mapped_column(BigInteger, nullable=False)
    echeance: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    statut: Mapped[AvanceStatut] = mapped_column(
        SAEnum(AvanceStatut, native_enum=False, length=20),
        nullable=False,
        default=AvanceStatut.AVANCEE,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
