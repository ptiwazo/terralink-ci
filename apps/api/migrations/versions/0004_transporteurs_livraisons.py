"""Phase 3 : transporteurs + livraisons

Revision ID: 0004_transporteurs_livraisons
Revises: 0003_escrow_ledger
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0004_transporteurs_livraisons"
down_revision: Union[str, None] = "0003_escrow_ledger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRANSPORTEUR_STATUT = sa.Enum(
    "EN_ATTENTE", "VALIDE", "REJETE",
    native_enum=False, length=20, name="transporteur_statut",
)
LIVRAISON_STATUT = sa.Enum(
    "ASSIGNEE", "EN_COURS", "LIVREE",
    native_enum=False, length=20, name="livraison_statut",
)


def upgrade() -> None:
    op.create_table(
        "transporteurs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("vehicule", sa.String(length=120), nullable=False),
        sa.Column("immatriculation", sa.String(length=40), nullable=False),
        sa.Column("caution_deposee", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("statut", TRANSPORTEUR_STATUT, nullable=False),
        sa.Column("note", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transporteurs_statut", "transporteurs", ["statut"])

    op.create_table(
        "livraisons",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("commande_id", UUID(as_uuid=True), sa.ForeignKey("commandes.id"), nullable=False, unique=True),
        sa.Column("transporteur_id", UUID(as_uuid=True), sa.ForeignKey("transporteurs.id"), nullable=False),
        sa.Column("statut", LIVRAISON_STATUT, nullable=False),
        sa.Column("code_remise_hash", sa.String(length=255), nullable=False),
        sa.Column("assurance_ref", sa.String(length=60), nullable=True),
        sa.Column("gps_traces", JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("livree_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_livraisons_transporteur_id", "livraisons", ["transporteur_id"])
    op.create_index("ix_livraisons_statut", "livraisons", ["statut"])


def downgrade() -> None:
    op.drop_table("livraisons")
    op.drop_table("transporteurs")
