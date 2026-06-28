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
