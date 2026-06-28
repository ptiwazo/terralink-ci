"""Schémas Pydantic pour l'escrow et les webhooks de paiement."""
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import EscrowStatut


class EscrowPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    commande_id: uuid.UUID
    montant: int
    commission: int
    montant_net: int
    statut: EscrowStatut
    ref_depot: str | None
    ref_paiement: str | None


class WebhookPaiement(BaseModel):
    """Événement entrant du fournisseur de paiement (authentifié par signature)."""

    type: str
    ref_transaction: str
    idempotency_key: str
    montant: int
    signature: str
