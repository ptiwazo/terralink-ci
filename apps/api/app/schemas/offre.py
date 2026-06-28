"""Schémas Pydantic pour les offres (stocks)."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OffreStatut
from app.schemas.produit import ProduitPublic


class ProducteurMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nom: str


class OffreCreate(BaseModel):
    produit_id: uuid.UUID
    quantite_disponible: int = Field(gt=0)
    prix_unitaire: int = Field(gt=0, description="Prix unitaire en FCFA (entier)")
    qualite: str | None = Field(default=None, max_length=120)
    dispo_le: date
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)


class OffreUpdate(BaseModel):
    quantite_disponible: int | None = Field(default=None, ge=0)
    prix_unitaire: int | None = Field(default=None, gt=0)
    qualite: str | None = Field(default=None, max_length=120)
    dispo_le: date | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    statut: OffreStatut | None = None


class OffrePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    producteur_id: uuid.UUID
    produit: ProduitPublic
    producteur: ProducteurMini
    quantite_disponible: int
    prix_unitaire: int
    qualite: str | None
    dispo_le: date
    lat: float | None
    lng: float | None
    statut: OffreStatut
    created_at: datetime


class OffreCatalogueItem(BaseModel):
    """Offre enrichie de la distance (recherche acheteur)."""

    offre: OffrePublic
    distance_km: float | None
