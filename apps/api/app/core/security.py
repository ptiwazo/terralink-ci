"""Hash de mots de passe (Argon2) et émission/validation de JWT.

- Mots de passe hachés avec Argon2 (CLAUDE.md §3 : Argon2 ou bcrypt).
- Deux types de jetons : `access` (court) et `refresh` (long), tous deux JWT
  signés HS256. Le champ `type` distingue les deux pour éviter qu'un refresh
  serve d'access et inversement.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ACCESS_TYPE = "access"
REFRESH_TYPE = "refresh"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    return _create_token(
        subject,
        ACCESS_TYPE,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        REFRESH_TYPE,
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Décode et valide un JWT. Lève `JWTError` si invalide/expiré/mauvais type."""
    payload = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type:
        raise JWTError("Type de jeton inattendu")
    return payload
