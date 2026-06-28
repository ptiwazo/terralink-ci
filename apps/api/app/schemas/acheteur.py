"""Schémas Pydantic pour les acheteurs et l'éligibilité au crédit."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AcheteurType


class AcheteurCreate(BaseModel):
    type: AcheteurType
    adresse: str | None = Field(default=None, max_length=255)


class AcheteurPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    type: AcheteurType
    adresse: str | None
    plafond_credit: int


class PlafondRequest(BaseModel):
    plafond_credit: int = Field(ge=0)


class EligibilitePublic(BaseModel):
    """Synthèse de la capacité de crédit d'un acheteur (paiement différé)."""

    score: int                # nb de commandes comptant menées à terme
    plafond_credit: int       # plafond accordé manuellement (OPS)
    plafond_suggere: int      # plafond issu du scoring
    plafond_effectif: int     # max des deux
    encours: int              # créances en cours (AVANCEE + IMPAYEE)
    disponible: int           # plafond_effectif − encours
