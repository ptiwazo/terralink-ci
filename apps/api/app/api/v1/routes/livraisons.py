"""Routes des livraisons : assignation (code de remise), expédition implicite,
traçabilité GPS, confirmation par code, et résolution de litige.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.commande import CommandePublic
from app.schemas.livraison import (
    AssignationResponse,
    AssignerRequest,
    ConfirmerReceptionRequest,
    LivraisonPublic,
    NotationRequest,
    PositionRequest,
    ResolutionRequest,
)
from app.services import commande_service, livraison_service
from app.services.commande_service import CommandeError
from app.services.livraison_service import LivraisonError

router = APIRouter(prefix="/commandes", tags=["livraisons"])


@router.post("/{commande_id}/assigner-transporteur", response_model=AssignationResponse)
def assigner(
    commande_id: uuid.UUID,
    data: AssignerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        livraison, code = livraison_service.assigner(
            db, commande_id, data.transporteur_id, user
        )
    except LivraisonError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return AssignationResponse(livraison=livraison, code_remise=code)


@router.get("/{commande_id}/livraison", response_model=LivraisonPublic)
def detail_livraison(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        commande_service.obtenir_commande(db, commande_id, user)  # contrôle d'accès
    except CommandeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    livraison = livraison_service.get_livraison(db, commande_id)
    if livraison is None:
        raise HTTPException(status_code=404, detail="Aucune livraison")
    return livraison


@router.post("/{commande_id}/position", response_model=LivraisonPublic)
def ajouter_position(
    commande_id: uuid.UUID,
    data: PositionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return livraison_service.ajouter_position(db, commande_id, user, data.lat, data.lng)
    except LivraisonError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/{commande_id}/noter-transporteur", response_model=LivraisonPublic)
def noter_transporteur(
    commande_id: uuid.UUID,
    data: NotationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return livraison_service.noter_transporteur(db, commande_id, user, data.note)
    except LivraisonError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/{commande_id}/confirmer-reception", response_model=CommandePublic)
def confirmer_reception(
    commande_id: uuid.UUID,
    data: ConfirmerReceptionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return livraison_service.confirmer_reception(db, commande_id, user, data.code)
    except LivraisonError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/{commande_id}/resoudre", response_model=CommandePublic)
def resoudre_litige(
    commande_id: uuid.UUID,
    data: ResolutionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    if data.sens not in ("REMBOURSE", "LIBERE"):
        raise HTTPException(status_code=422, detail="sens doit être REMBOURSE ou LIBERE")
    try:
        return commande_service.resoudre_litige(db, commande_id, user, data.sens)
    except CommandeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
