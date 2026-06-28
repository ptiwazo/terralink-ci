"""Schémas Pydantic pour les livraisons."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LivraisonStatut


class AssignerRequest(BaseModel):
    transporteur_id: uuid.UUID


class ConfirmerReceptionRequest(BaseModel):
    code: str = Field(min_length=4, max_length=12)


class PositionRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class ResolutionRequest(BaseModel):
    sens: str = Field(description="REMBOURSE (acheteur) ou LIBERE (producteur)")


class NotationRequest(BaseModel):
    note: int = Field(ge=1, le=5)


class LivraisonPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    commande_id: uuid.UUID
    transporteur_id: uuid.UUID
    statut: LivraisonStatut
    assurance_ref: str | None
    gps_traces: list
    livree_at: datetime | None
    note_transporteur: int | None


class AssignationResponse(BaseModel):
    """L'unique occasion de voir le code de remise en clair (à remettre au
    transporteur). Ensuite, seul le hash est conservé."""

    livraison: LivraisonPublic
    code_remise: str


class CoursePublic(BaseModel):
    """Une course du transporteur : la livraison + un résumé de la commande."""

    livraison: LivraisonPublic
    commande_id: uuid.UUID
    commande_statut: str
    montant: int
    produits: str
