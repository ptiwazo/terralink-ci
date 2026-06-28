"""Schémas Pydantic pour l'utilisateur (sortie publique uniquement)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Role, UserStatus


class UserPublic(BaseModel):
    """Représentation renvoyée au client. JAMAIS le hash du mot de passe."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    telephone: str
    nom: str
    email: str | None
    role: Role
    statut: UserStatus
    created_at: datetime
