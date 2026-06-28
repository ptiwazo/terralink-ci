"""Schémas Pydantic pour les abonnements premium."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AbonnementFormule, AbonnementStatut


class AbonnementCreate(BaseModel):
    formule: AbonnementFormule = AbonnementFormule.PREMIUM


class AbonnementPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    formule: AbonnementFormule
    debut: datetime
    fin: datetime
    prix: int
    statut: AbonnementStatut
