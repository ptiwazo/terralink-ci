"""Routes trésorerie : remboursement de créance, suivi des impayés."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.avance import AvancePublic
from app.services import commande_service, tresorerie_service
from app.services.commande_service import CommandeError
from app.services.tresorerie_service import TresorerieError

router = APIRouter(tags=["tresorerie"])


@router.get("/commandes/{commande_id}/avance", response_model=AvancePublic)
def detail_avance(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        commande_service.obtenir_commande(db, commande_id, user)  # contrôle d'accès
    except CommandeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    avance = tresorerie_service.get_avance(db, commande_id)
    if avance is None:
        raise HTTPException(status_code=404, detail="Aucune avance")
    return avance


@router.post("/commandes/{commande_id}/rembourser-creance", response_model=AvancePublic)
def rembourser_creance(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return tresorerie_service.rembourser_creance(db, commande_id, user)
    except TresorerieError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/tresorerie/impayes", response_model=list[AvancePublic])
def impayes(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    return tresorerie_service.lister_impayes(db)


@router.post("/tresorerie/marquer-impayes")
def marquer_impayes(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    nb = tresorerie_service.marquer_impayes(db, user)
    return {"impayes_marques": nb}
