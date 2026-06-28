"""Routes des offres (stocks) — CRUD réservé au producteur propriétaire."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.offre import OffreCreate, OffrePublic, OffreUpdate
from app.services import offre_service
from app.services.offre_service import OffreError

router = APIRouter(prefix="/offres", tags=["offres"])


def _handle(exc: OffreError):
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("", response_model=OffrePublic, status_code=status.HTTP_201_CREATED)
def creer_offre(
    data: OffreCreate,
    db: Session = Depends(get_db),
    producteur: User = Depends(require_roles(Role.PRODUCTEUR)),
):
    try:
        return offre_service.creer_offre(db, producteur, data)
    except OffreError as exc:
        _handle(exc)


@router.get("/mes", response_model=list[OffrePublic])
def mes_offres(
    db: Session = Depends(get_db),
    producteur: User = Depends(require_roles(Role.PRODUCTEUR)),
):
    return offre_service.lister_mes_offres(db, producteur)


@router.get("/{offre_id}", response_model=OffrePublic)
def detail_offre(
    offre_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return offre_service.obtenir_offre(db, offre_id)
    except OffreError as exc:
        _handle(exc)


@router.patch("/{offre_id}", response_model=OffrePublic)
def maj_offre(
    offre_id: uuid.UUID,
    data: OffreUpdate,
    db: Session = Depends(get_db),
    producteur: User = Depends(require_roles(Role.PRODUCTEUR)),
):
    try:
        return offre_service.maj_offre(db, offre_id, producteur, data)
    except OffreError as exc:
        _handle(exc)


@router.delete("/{offre_id}", response_model=OffrePublic)
def retirer_offre(
    offre_id: uuid.UUID,
    db: Session = Depends(get_db),
    producteur: User = Depends(require_roles(Role.PRODUCTEUR)),
):
    try:
        return offre_service.retirer_offre(db, offre_id, producteur)
    except OffreError as exc:
        _handle(exc)
