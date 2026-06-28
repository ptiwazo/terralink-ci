"""Recherche du catalogue côté acheteur (CLAUDE.md §1, Phase 1).

Filtres : produit, proximité géographique, délai de disponibilité.
La distance est calculée par formule de Haversine en Python — suffisant pour
le pilote. Une montée en charge passerait par PostGIS / l'extension earthdistance.
"""
import math
import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import OffreStatut
from app.models.offre import Offre


@dataclass
class ResultatCatalogue:
    offre: Offre
    distance_km: float | None


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0  # rayon terrestre moyen en km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def rechercher(
    db: Session,
    *,
    produit_id: uuid.UUID | None = None,
    dispo_avant: date | None = None,
    lat: float | None = None,
    lng: float | None = None,
    rayon_km: float | None = None,
) -> list[ResultatCatalogue]:
    stmt = select(Offre).where(
        Offre.statut == OffreStatut.DISPONIBLE,
        Offre.quantite_disponible > 0,
    )
    if produit_id is not None:
        stmt = stmt.where(Offre.produit_id == produit_id)
    if dispo_avant is not None:
        stmt = stmt.where(Offre.dispo_le <= dispo_avant)

    offres = list(db.scalars(stmt))

    resultats: list[ResultatCatalogue] = []
    for offre in offres:
        distance = None
        if lat is not None and lng is not None and offre.lat is not None and offre.lng is not None:
            distance = _haversine_km(lat, lng, offre.lat, offre.lng)
            if rayon_km is not None and distance > rayon_km:
                continue
        resultats.append(ResultatCatalogue(offre=offre, distance_km=distance))

    # Tri : par distance si géoloc fournie, sinon par disponibilité la plus proche.
    if lat is not None and lng is not None:
        resultats.sort(key=lambda r: (r.distance_km is None, r.distance_km or 0.0))
    else:
        resultats.sort(key=lambda r: r.offre.dispo_le)
    return resultats
