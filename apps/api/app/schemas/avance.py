"""Schémas Pydantic pour les avances de trésorerie."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AvanceStatut


class AvancePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    commande_id: uuid.UUID
    acheteur_id: uuid.UUID
    montant: int
    montant_avance: int
    commission: int
    decote: int
    echeance: datetime
    statut: AvanceStatut
