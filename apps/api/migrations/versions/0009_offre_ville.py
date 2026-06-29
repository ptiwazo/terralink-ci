"""Ville de l'offre (saisie producteur via ville + carte)

Revision ID: 0009_offre_ville
Revises: 0008_acheteur_geoloc
Create Date: 2026-06-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_offre_ville"
down_revision: Union[str, None] = "0008_acheteur_geoloc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("offres", sa.Column("ville", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("offres", "ville")
