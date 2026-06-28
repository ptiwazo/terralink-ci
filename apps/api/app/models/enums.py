"""Énumérations métier partagées.

Les rôles correspondent exactement à CLAUDE.md §2.2.
"""
import enum


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    OPS = "OPS"
    PRODUCTEUR = "PRODUCTEUR"
    ACHETEUR = "ACHETEUR"
    TRANSPORTEUR = "TRANSPORTEUR"


class UserStatus(str, enum.Enum):
    ACTIF = "ACTIF"
    SUSPENDU = "SUSPENDU"


class Unite(str, enum.Enum):
    """Unités de vente des produits agricoles."""

    KG = "KG"
    TONNE = "TONNE"
    SAC = "SAC"
    REGIME = "REGIME"  # ex: régime de banane plantain
    CASIER = "CASIER"
    UNITE = "UNITE"
    LITRE = "LITRE"


class OffreStatut(str, enum.Enum):
    DISPONIBLE = "DISPONIBLE"
    EPUISEE = "EPUISEE"
    RETIREE = "RETIREE"


class ModePaiement(str, enum.Enum):
    COMPTANT = "COMPTANT"
    DIFFERE = "DIFFERE"


class EscrowStatut(str, enum.Enum):
    """Cycle de vie du séquestre d'une commande (CLAUDE.md §4)."""

    EN_ATTENTE = "EN_ATTENTE"  # dépôt initié, en attente de confirmation
    SEQUESTRE = "SEQUESTRE"    # fonds bloqués (dépôt confirmé)
    LIBERE = "LIBERE"          # fonds libérés au producteur
    REMBOURSE = "REMBOURSE"    # fonds remboursés à l'acheteur (litige, Phase 3)


class CommandeStatut(str, enum.Enum):
    """Statuts de la machine à états des commandes (CLAUDE.md §5).

    Phase 1 implémente le parcours jusqu'à LIVREE_CONFORME, sans argent réel
    (le passage par PAYEE_SEQUESTRE est *simulé*). Les statuts liés aux fonds
    (FONDS_LIBERES, CLOTUREE) et au litige arrivent en Phases 2-3.
    """

    CREEE = "CREEE"
    PAYEE_SEQUESTRE = "PAYEE_SEQUESTRE"
    AVANCE_VERSEE = "AVANCE_VERSEE"
    EN_PREPARATION = "EN_PREPARATION"
    EN_LIVRAISON = "EN_LIVRAISON"
    LIVREE_CONFORME = "LIVREE_CONFORME"
    LITIGE = "LITIGE"
    FONDS_LIBERES = "FONDS_LIBERES"
    CLOTUREE = "CLOTUREE"
    RESOLUE_REMBOURSEE = "RESOLUE_REMBOURSEE"
    RESOLUE_LIBEREE = "RESOLUE_LIBEREE"
