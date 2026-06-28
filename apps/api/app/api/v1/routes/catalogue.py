"""Recherche du catalogue (acheteur) — produit, proximité, délai."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.offre import OffreCatalogueItem
from app.services import catalogue_service

router = APIRouter(prefix="/catalogue", tags=["catalogue"])


@router.get("", response_model=list[OffreCatalogueItem])
def rechercher(
    produit_id: uuid.UUID | None = Query(default=None),
    dispo_avant: date | None = Query(default=None),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    rayon_km: float | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[OffreCatalogueItem]:
    resultats = catalogue_service.rechercher(
        db,
        produit_id=produit_id,
        dispo_avant=dispo_avant,
        lat=lat,
        lng=lng,
        rayon_km=rayon_km,
    )
    return [
        OffreCatalogueItem(offre=r.offre, distance_km=r.distance_km) for r in resultats
    ]
