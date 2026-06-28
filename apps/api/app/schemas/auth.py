"""Schémas d'entrée/sortie pour l'authentification."""
from pydantic import BaseModel, Field, field_validator

from app.models.enums import Role
from app.schemas.user import UserPublic


class RegisterRequest(BaseModel):
    telephone: str = Field(min_length=8, max_length=20)
    nom: str = Field(min_length=2, max_length=120)
    mot_de_passe: str = Field(min_length=8, max_length=128)
    role: Role
    email: str | None = Field(default=None, max_length=255)

    @field_validator("telephone")
    @classmethod
    def telephone_chiffres(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "")
        if not cleaned.lstrip("+").isdigit():
            raise ValueError("Le téléphone doit être numérique (ex: +2250700000000)")
        return cleaned

    @field_validator("role")
    @classmethod
    def role_inscriptible(cls, v: Role) -> Role:
        # ADMIN / OPS ne s'auto-inscrivent pas : créés par l'équipe interne.
        if v in (Role.ADMIN, Role.OPS):
            raise ValueError("Ce rôle ne peut pas être créé par auto-inscription")
        return v


class LoginRequest(BaseModel):
    telephone: str
    mot_de_passe: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserPublic
    tokens: TokenPair
