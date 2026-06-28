"""Agrège les routes de l'API v1 sous /api/v1."""
from fastapi import APIRouter

from app.api.v1.routes import (
    acheteurs,
    analytics,
    auth,
    catalogue,
    commandes,
    dashboard,
    factures,
    livraisons,
    offres,
    paiements,
    premium,
    produits,
    transporteurs,
    tresorerie,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.router)
api_router.include_router(produits.router)
api_router.include_router(offres.router)
api_router.include_router(catalogue.router)
api_router.include_router(commandes.router)
api_router.include_router(paiements.router)
api_router.include_router(transporteurs.router)
api_router.include_router(livraisons.router)
api_router.include_router(acheteurs.router)
api_router.include_router(tresorerie.router)
api_router.include_router(factures.router)
api_router.include_router(premium.router)
api_router.include_router(analytics.router)
