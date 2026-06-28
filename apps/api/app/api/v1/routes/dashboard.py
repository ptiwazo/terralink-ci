"""Tableau de bord par rôle (Phase 0 : contenu vide, structuré par rôle).

Livrable Phase 0 : un utilisateur connecté voit un tableau de bord adapté
à son rôle. Le contenu réel sera rempli aux phases suivantes.
"""
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models.enums import Role
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Sections de navigation prévues par rôle (squelette, cf. phases 1-5).
SECTIONS_PAR_ROLE: dict[Role, list[str]] = {
    Role.ADMIN: ["Utilisateurs", "Commandes", "Trésorerie", "Audit", "KPIs"],
    Role.OPS: ["Commandes", "Livraisons", "Litiges", "Transporteurs"],
    Role.PRODUCTEUR: ["Mes offres", "Mes commandes", "Mes paiements"],
    Role.ACHETEUR: ["Catalogue", "Mes commandes", "Mes factures"],
    Role.TRANSPORTEUR: ["Mes courses", "Livraisons à confirmer"],
}


@router.get("")
def get_dashboard(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "role": current_user.role.value,
        "nom": current_user.nom,
        "sections": SECTIONS_PAR_ROLE.get(current_user.role, []),
        "message": "Bienvenue sur TerraLink CI. (Phase 0 — tableau de bord vide)",
    }
