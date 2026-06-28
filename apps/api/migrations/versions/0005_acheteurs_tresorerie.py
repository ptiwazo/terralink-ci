"""Phase 4 : acheteurs + avances_tresorerie

Revision ID: 0005_acheteurs_tresorerie
Revises: 0004_transporteurs_livraisons
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0005_acheteurs_tresorerie"
down_revision: Union[str, None] = "0004_transporteurs_livraisons"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACHETEUR_TYPE = sa.Enum(
    "HOTEL", "RESTAURANT", "SUPERMARCHE", "USINE", "AUTRE",
    native_enum=False, length=20, name="acheteur_type",
)
AVANCE_STATUT = sa.Enum(
    "AVANCEE", "REMBOURSEE", "IMPAYEE", "ANNULEE",
    native_enum=False, length=20, name="avance_statut",
)


def upgrade() -> None:
    op.create_table(
        "acheteurs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("type", ACHETEUR_TYPE, nullable=False),
        sa.Column("adresse", sa.String(length=255), nullable=True),
        sa.Column("plafond_credit", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "avances_tresorerie",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("commande_id", UUID(as_uuid=True), sa.ForeignKey("commandes.id"), nullable=False, unique=True),
        sa.Column("acheteur_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("montant", sa.BigInteger(), nullable=False),
        sa.Column("montant_avance", sa.BigInteger(), nullable=False),
        sa.Column("commission", sa.BigInteger(), nullable=False),
        sa.Column("decote", sa.BigInteger(), nullable=False),
        sa.Column("echeance", sa.DateTime(timezone=True), nullable=False),
        sa.Column("statut", AVANCE_STATUT, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_avances_acheteur_id", "avances_tresorerie", ["acheteur_id"])
    op.create_index("ix_avances_statut", "avances_tresorerie", ["statut"])


def downgrade() -> None:
    op.drop_table("avances_tresorerie")
    op.drop_table("acheteurs")
