"""Phase 2 : escrow_transactions + ledger_entries (append-only)

Revision ID: 0003_escrow_ledger
Revises: 0002_catalogue_commandes
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003_escrow_ledger"
down_revision: Union[str, None] = "0002_catalogue_commandes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ESCROW_STATUT = sa.Enum(
    "EN_ATTENTE", "SEQUESTRE", "LIBERE", "REMBOURSE",
    native_enum=False, length=20, name="escrow_statut",
)


def upgrade() -> None:
    op.create_table(
        "escrow_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("commande_id", UUID(as_uuid=True), sa.ForeignKey("commandes.id"), nullable=False, unique=True),
        sa.Column("montant", sa.BigInteger(), nullable=False),
        sa.Column("commission", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("montant_net", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("statut", ESCROW_STATUT, nullable=False),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False, unique=True),
        sa.Column("ref_depot", sa.String(length=120), nullable=True),
        sa.Column("ref_paiement", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_escrow_statut", "escrow_transactions", ["statut"])

    op.create_table(
        "ledger_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("compte", sa.String(length=80), nullable=False),
        sa.Column("contrepartie", sa.String(length=80), nullable=True),
        sa.Column("montant", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("ref_commande", UUID(as_uuid=True), nullable=True),
        sa.Column("ref_idempotence", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ref_idempotence", "compte", name="uq_ledger_idem_compte"),
    )
    op.create_index("ix_ledger_entries_compte", "ledger_entries", ["compte"])
    op.create_index("ix_ledger_entries_ref_commande", "ledger_entries", ["ref_commande"])
    op.create_index("ix_ledger_entries_ref_idempotence", "ledger_entries", ["ref_idempotence"])


def downgrade() -> None:
    op.drop_table("ledger_entries")
    op.drop_table("escrow_transactions")
