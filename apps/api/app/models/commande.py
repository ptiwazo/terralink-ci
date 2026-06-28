"""Tables `commandes` et `lignes_commande`.

- Une commande s'adresse à **un seul producteur** (CLAUDE.md §4 : champ
  producteur_id). Toutes les lignes proviennent d'offres de ce producteur.
- `montant_total` et `prix_unitaire` en **entiers FCFA**. Le montant est
  TOUJOURS recalculé côté serveur (CLAUDE.md §2.1) — jamais reçu du client.
- `prix_unitaire` de la ligne est figé (snapshot) au moment de la commande.
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import CommandeStatut, ModePaiement


class Commande(Base):
    __tablename__ = "commandes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    acheteur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    producteur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    statut: Mapped[CommandeStatut] = mapped_column(
        SAEnum(CommandeStatut, native_enum=False, length=30),
        nullable=False,
        default=CommandeStatut.CREEE,
        index=True,
    )
    montant_total: Mapped[int] = mapped_column(BigInteger, nullable=False)  # FCFA
    mode_paiement: Mapped[ModePaiement] = mapped_column(
        SAEnum(ModePaiement, native_enum=False, length=20), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    lignes: Mapped[list["LigneCommande"]] = relationship(
        back_populates="commande", lazy="joined", cascade="all, delete-orphan"
    )


class LigneCommande(Base):
    __tablename__ = "lignes_commande"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    commande_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commandes.id"), nullable=False, index=True
    )
    offre_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("offres.id"), nullable=False
    )
    produit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produits.id"), nullable=False
    )
    quantite: Mapped[int] = mapped_column(BigInteger, nullable=False)
    prix_unitaire: Mapped[int] = mapped_column(BigInteger, nullable=False)  # FCFA figé

    commande: Mapped["Commande"] = relationship(back_populates="lignes")
    produit: Mapped["Produit"] = relationship(lazy="joined")  # noqa: F821
