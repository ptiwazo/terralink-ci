"""Routes des commandes : création (acheteur), suivi, transitions d'état."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.commande import CommandeCreate, CommandePublic, TransitionRequest
from app.services import commande_service
from app.services.commande_service import CommandeError

router = APIRouter(prefix="/commandes", tags=["commandes"])


def _handle(exc: CommandeError):
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("", response_model=CommandePublic, status_code=status.HTTP_201_CREATED)
def creer_commande(
    data: CommandeCreate,
    db: Session = Depends(get_db),
    acheteur: User = Depends(require_roles(Role.ACHETEUR)),
):
    try:
        return commande_service.creer_commande(db, acheteur, data)
    except CommandeError as exc:
        _handle(exc)


@router.get("/mes", response_model=list[CommandePublic])
def mes_commandes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return commande_service.lister_mes_commandes(db, user)


@router.get("/{commande_id}", response_model=CommandePublic)
def detail_commande(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return commande_service.obtenir_commande(db, commande_id, user)
    except CommandeError as exc:
        _handle(exc)


@router.post("/{commande_id}/transition", response_model=CommandePublic)
def transition_commande(
    commande_id: uuid.UUID,
    data: TransitionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return commande_service.appliquer_transition(db, commande_id, user, data.action)
    except CommandeError as exc:
        _handle(exc)
