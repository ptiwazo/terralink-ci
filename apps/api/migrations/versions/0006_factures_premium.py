"""Phase 5 : factures (OHADA) + séquences + abonnements premium

Revision ID: 0006_factures_premium
Revises: 0005_acheteurs_tresorerie
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0006_factures_premium"
down_revision: Union[str, None] = "0005_acheteurs_tresorerie"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ABONNEMENT_FORMULE = sa.Enum(
    "STANDARD", "PREMIUM", native_enum=False, length=20, name="abonnement_formule",
)
ABONNEMENT_STATUT = sa.Enum(
    "ACTIF", "EXPIRE", "ANNULE", native_enum=False, length=20, name="abonnement_statut",
)


def upgrade() -> None:
    op.create_table(
        "facture_sequences",
        sa.Column("exercice", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("dernier_numero", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "factures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("numero", sa.String(length=30), nullable=False, unique=True),
        sa.Column("exercice", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("commande_id", UUID(as_uuid=True), sa.ForeignKey("commandes.id"), nullable=False, unique=True),
        sa.Column("montant_ht", sa.BigInteger(), nullable=False),
        sa.Column("tva", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("montant_ttc", sa.BigInteger(), nullable=False),
        sa.Column("pdf_ref", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_factures_exercice", "factures", ["exercice"])

    op.create_table(
        "abonnements_premium",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("acheteur_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("formule", ABONNEMENT_FORMULE, nullable=False),
        sa.Column("debut", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prix", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("statut", ABONNEMENT_STATUT, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_abonnements_acheteur_id", "abonnements_premium", ["acheteur_id"])
    op.create_index("ix_abonnements_statut", "abonnements_premium", ["statut"])


def downgrade() -> None:
    op.drop_table("abonnements_premium")
    op.drop_table("factures")
    op.drop_table("facture_sequences")
