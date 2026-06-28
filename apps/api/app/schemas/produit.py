"""Schémas Pydantic pour le catalogue de référence."""
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import Unite


class ProduitPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nom: str
    categorie: str
    unite: Unite
