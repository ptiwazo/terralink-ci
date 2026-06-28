"""Schémas Pydantic pour les commandes."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CommandeStatut, ModePaiement
from app.schemas.produit import ProduitPublic


class LigneCreate(BaseModel):
    offre_id: uuid.UUID
    quantite: int = Field(gt=0)


class CommandeCreate(BaseModel):
    lignes: list[LigneCreate] = Field(min_length=1)
    mode_paiement: ModePaiement = ModePaiement.COMPTANT


class LignePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    offre_id: uuid.UUID
    produit: ProduitPublic
    quantite: int
    prix_unitaire: int


class CommandePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    acheteur_id: uuid.UUID
    producteur_id: uuid.UUID
    statut: CommandeStatut
    montant_total: int
    mode_paiement: ModePaiement
    lignes: list[LignePublic]
    created_at: datetime
    updated_at: datetime


class TransitionRequest(BaseModel):
    action: str = Field(description="Nom de la transition (ex: SIMULER_PAIEMENT)")
