"""Routes d'authentification : inscription, connexion, rafraîchissement.

Ce sont les SEULES routes publiques (CLAUDE.md §2.2).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import REFRESH_TYPE, create_access_token, decode_token
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.user import UserPublic
from app.services import auth_service
from app.services.auth_service import AuthError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user, tokens = auth_service.register(db, data)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user, tokens = auth_service.authenticate(db, data.telephone, data.mot_de_passe)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        payload = decode_token(data.refresh_token, REFRESH_TYPE)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré",
        )
    user = auth_service.get_user_by_id(db, payload.get("sub", ""))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable"
        )
    # On ré-émet un access token; le refresh fourni reste valide jusqu'à son exp.
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=data.refresh_token,
    )
