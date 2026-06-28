"""Création initiale : table users

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("telephone", sa.String(length=20), nullable=False),
        sa.Column("nom", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("mot_de_passe_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "ADMIN",
                "OPS",
                "PRODUCTEUR",
                "ACHETEUR",
                "TRANSPORTEUR",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column(
            "statut",
            sa.Enum("ACTIF", "SUSPENDU", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_telephone", "users", ["telephone"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_telephone", table_name="users")
    op.drop_table("users")
