"""Table `livraisons` — une livraison par commande (CLAUDE.md §4).

`code_remise_hash` : le code de remise n'est JAMAIS stocké en clair (haché comme
un mot de passe). `gps_traces` : suite simple de positions {lat,lng,ts}.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import LivraisonStatut


class Livraison(Base):
    __tablename__ = "livraisons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    commande_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commandes.id"), nullable=False, unique=True
    )
    transporteur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transporteurs.id"), nullable=False, index=True
    )
    statut: Mapped[LivraisonStatut] = mapped_column(
        SAEnum(LivraisonStatut, native_enum=False, length=20),
        nullable=False,
        default=LivraisonStatut.ASSIGNEE,
        index=True,
    )
    code_remise_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    assurance_ref: Mapped[str | None] = mapped_column(String(60), nullable=True)
    gps_traces: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    livree_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
