"""Logique d'authentification : inscription, connexion, rafraîchissement.

Toute la vérification (unicité du téléphone, validité du mot de passe,
statut du compte) est faite ici, côté serveur (CLAUDE.md §2.2).
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserStatus
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenPair


class AuthError(Exception):
    """Erreur métier d'authentification (mappée en HTTP par la route)."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _tokens_for(user: User) -> TokenPair:
    subject = str(user.id)
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


def register(db: Session, data: RegisterRequest) -> tuple[User, TokenPair]:
    existing = db.scalar(select(User).where(User.telephone == data.telephone))
    if existing is not None:
        raise AuthError("Ce numéro de téléphone est déjà utilisé", status_code=409)

    user = User(
        telephone=data.telephone,
        nom=data.nom,
        email=data.email,
        mot_de_passe_hash=hash_password(data.mot_de_passe),
        role=data.role,
        statut=UserStatus.ACTIF,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, _tokens_for(user)


def authenticate(db: Session, telephone: str, mot_de_passe: str) -> tuple[User, TokenPair]:
    user = db.scalar(select(User).where(User.telephone == telephone))
    # Message volontairement générique pour ne pas révéler l'existence d'un compte.
    if user is None or not verify_password(mot_de_passe, user.mot_de_passe_hash):
        raise AuthError("Identifiants invalides", status_code=401)
    if user.statut != UserStatus.ACTIF:
        raise AuthError("Compte suspendu", status_code=403)
    return user, _tokens_for(user)


def get_user_by_id(db: Session, user_id: str) -> User | None:
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        return None
    return db.get(User, uid)
