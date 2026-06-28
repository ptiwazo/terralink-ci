"""Coordonnées de livraison de l'acheteur (suivi/ETA)

Revision ID: 0008_acheteur_geoloc
Revises: 0007_note_transporteur
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_acheteur_geoloc"
down_revision: Union[str, None] = "0007_note_transporteur"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("acheteurs", sa.Column("lat", sa.Float(), nullable=True))
    op.add_column("acheteurs", sa.Column("lng", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("acheteurs", "lng")
    op.drop_column("acheteurs", "lat")
