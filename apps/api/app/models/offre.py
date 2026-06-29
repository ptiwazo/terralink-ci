"""Table `offres` (stocks) publiées par les producteurs.

- `prix_unitaire` est en **entiers FCFA** (BigInteger). Jamais de float pour
  l'argent (CLAUDE.md §2.3).
- `lat`/`lng` sont des coordonnées (float autorisé : ce ne sont pas des montants).
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import OffreStatut


class Offre(Base):
    __tablename__ = "offres"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    producteur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    produit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produits.id"), nullable=False, index=True
    )

    quantite_disponible: Mapped[int] = mapped_column(BigInteger, nullable=False)
    prix_unitaire: Mapped[int] = mapped_column(BigInteger, nullable=False)  # FCFA
    qualite: Mapped[str | None] = mapped_column(String(120), nullable=True)
    dispo_le: Mapped[date] = mapped_column(Date, nullable=False)

    ville: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    statut: Mapped[OffreStatut] = mapped_column(
        SAEnum(OffreStatut, native_enum=False, length=20),
        nullable=False,
        default=OffreStatut.DISPONIBLE,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    produit: Mapped["Produit"] = relationship(lazy="joined")  # noqa: F821
    producteur: Mapped["User"] = relationship(lazy="joined")  # noqa: F821
