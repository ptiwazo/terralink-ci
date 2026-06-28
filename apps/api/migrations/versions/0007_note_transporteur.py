"""Notation du transporteur : livraisons.note_transporteur

Revision ID: 0007_note_transporteur
Revises: 0006_factures_premium
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_note_transporteur"
down_revision: Union[str, None] = "0006_factures_premium"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("livraisons", sa.Column("note_transporteur", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("livraisons", "note_transporteur")
