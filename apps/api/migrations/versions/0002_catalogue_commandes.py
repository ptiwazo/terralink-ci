"""Phase 1 : produits, offres, commandes, lignes_commande, audit_log (+ seed produits)

Revision ID: 0002_catalogue_commandes
Revises: 0001_initial
Create Date: 2026-06-28
"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0002_catalogue_commandes"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UNITE = sa.Enum(
    "KG", "TONNE", "SAC", "REGIME", "CASIER", "UNITE", "LITRE",
    native_enum=False, length=20, name="unite",
)
OFFRE_STATUT = sa.Enum(
    "DISPONIBLE", "EPUISEE", "RETIREE",
    native_enum=False, length=20, name="offre_statut",
)
MODE_PAIEMENT = sa.Enum(
    "COMPTANT", "DIFFERE", native_enum=False, length=20, name="mode_paiement",
)
COMMANDE_STATUT = sa.Enum(
    "CREEE", "PAYEE_SEQUESTRE", "AVANCE_VERSEE", "EN_PREPARATION", "EN_LIVRAISON",
    "LIVREE_CONFORME", "LITIGE", "FONDS_LIBERES", "CLOTUREE",
    "RESOLUE_REMBOURSEE", "RESOLUE_LIBEREE",
    native_enum=False, length=30, name="commande_statut",
)

PRODUITS_SEED = [
    ("Manioc", "Tubercules", "KG"),
    ("Igname", "Tubercules", "KG"),
    ("Banane plantain", "Fruits", "REGIME"),
    ("Tomate", "Légumes", "KG"),
    ("Piment", "Légumes", "KG"),
    ("Poulet de chair", "Volaille", "UNITE"),
    ("Œufs de table", "Volaille", "CASIER"),
    ("Riz paddy", "Céréales", "SAC"),
    ("Maïs", "Céréales", "SAC"),
    ("Cacao", "Cultures de rente", "KG"),
    ("Huile de palme", "Transformés", "LITRE"),
    ("Attiéké", "Transformés", "KG"),
]


def upgrade() -> None:
    op.create_table(
        "produits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("nom", sa.String(length=120), nullable=False, unique=True),
        sa.Column("categorie", sa.String(length=60), nullable=False),
        sa.Column("unite", UNITE, nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "offres",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("producteur_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("produit_id", UUID(as_uuid=True), sa.ForeignKey("produits.id"), nullable=False),
        sa.Column("quantite_disponible", sa.BigInteger(), nullable=False),
        sa.Column("prix_unitaire", sa.BigInteger(), nullable=False),
        sa.Column("qualite", sa.String(length=120), nullable=True),
        sa.Column("dispo_le", sa.Date(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("statut", OFFRE_STATUT, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_offres_producteur_id", "offres", ["producteur_id"])
    op.create_index("ix_offres_produit_id", "offres", ["produit_id"])
    op.create_index("ix_offres_statut", "offres", ["statut"])

    op.create_table(
        "commandes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("acheteur_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("producteur_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("statut", COMMANDE_STATUT, nullable=False),
        sa.Column("montant_total", sa.BigInteger(), nullable=False),
        sa.Column("mode_paiement", MODE_PAIEMENT, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_commandes_acheteur_id", "commandes", ["acheteur_id"])
    op.create_index("ix_commandes_producteur_id", "commandes", ["producteur_id"])
    op.create_index("ix_commandes_statut", "commandes", ["statut"])

    op.create_table(
        "lignes_commande",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("commande_id", UUID(as_uuid=True), sa.ForeignKey("commandes.id"), nullable=False),
        sa.Column("offre_id", UUID(as_uuid=True), sa.ForeignKey("offres.id"), nullable=False),
        sa.Column("produit_id", UUID(as_uuid=True), sa.ForeignKey("produits.id"), nullable=False),
        sa.Column("quantite", sa.BigInteger(), nullable=False),
        sa.Column("prix_unitaire", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_lignes_commande_commande_id", "lignes_commande", ["commande_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("acteur_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("ressource_type", sa.String(length=40), nullable=False),
        sa.Column("ressource_id", UUID(as_uuid=True), nullable=True),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_log_acteur_id", "audit_log", ["acteur_id"])
    op.create_index("ix_audit_log_ressource_id", "audit_log", ["ressource_id"])

    # --- Seed du catalogue de référence ---
    produits_table = sa.table(
        "produits",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("nom", sa.String),
        sa.column("categorie", sa.String),
        sa.column("unite", sa.String),
        sa.column("actif", sa.Boolean),
    )
    op.bulk_insert(
        produits_table,
        [
            {"id": uuid.uuid4(), "nom": n, "categorie": c, "unite": u, "actif": True}
            for (n, c, u) in PRODUITS_SEED
        ],
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("lignes_commande")
    op.drop_table("commandes")
    op.drop_table("offres")
    op.drop_table("produits")
