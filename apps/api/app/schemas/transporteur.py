"""Schémas Pydantic pour les transporteurs."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TransporteurStatut


class TransporteurCreate(BaseModel):
    vehicule: str = Field(min_length=2, max_length=120)
    immatriculation: str = Field(min_length=2, max_length=40)
    caution_deposee: int = Field(ge=0, description="Caution en FCFA (entier)")


class TransporteurPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    vehicule: str
    immatriculation: str
    caution_deposee: int
    statut: TransporteurStatut
    note: float | None
