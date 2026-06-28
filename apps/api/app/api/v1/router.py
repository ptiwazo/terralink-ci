"""Agrège les routes de l'API v1 sous /api/v1."""
from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    catalogue,
    commandes,
    dashboard,
    offres,
    produits,
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
