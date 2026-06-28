"""Schémas Pydantic pour les factures."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FacturePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero: str
    exercice: int
    sequence: int
    commande_id: uuid.UUID
    montant_ht: int
    tva: int
    montant_ttc: int
    pdf_ref: str | None
    created_at: datetime
