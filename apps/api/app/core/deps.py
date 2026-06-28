"""Dépendances FastAPI : session DB, utilisateur courant, contrôle de rôle.

L'autorisation est TOUJOURS vérifiée côté serveur (CLAUDE.md §2.2) :
- `get_current_user` valide le jeton d'accès et charge l'utilisateur.
- `require_roles(...)` est une fabrique de dépendances qui rejette (403)
  tout rôle non autorisé sur une route.
"""
from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import ACCESS_TYPE, decode_token
from app.models.enums import Role, UserStatus
from app.models.user import User
from app.services.auth_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Jeton invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials, ACCESS_TYPE)
    except JWTError:
        raise invalid

    user = get_user_by_id(db, payload.get("sub", ""))
    if user is None:
        raise invalid
    if user.statut != UserStatus.ACTIF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Compte suspendu"
        )
    return user


def require_roles(*roles: Role):
    """Fabrique une dépendance qui n'autorise que les rôles fournis."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour ce rôle",
            )
        return current_user

    return checker
