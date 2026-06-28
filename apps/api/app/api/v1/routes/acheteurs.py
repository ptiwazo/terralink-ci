"""Routes acheteurs : profil + éligibilité au crédit (paiement différé)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.acheteur import (
    AcheteurCreate,
    AcheteurPublic,
    EligibilitePublic,
    PlafondRequest,
)
from app.services import acheteur_service
from app.services.acheteur_service import AcheteurError

router = APIRouter(prefix="/acheteurs", tags=["acheteurs"])


def _elig_public(e) -> EligibilitePublic:
    return EligibilitePublic(
        score=e.score,
        plafond_credit=e.plafond_credit,
        plafond_suggere=e.plafond_suggere,
        plafond_effectif=e.plafond_effectif,
        encours=e.encours,
        disponible=e.disponible,
    )


@router.post("/profil", response_model=AcheteurPublic, status_code=status.HTTP_201_CREATED)
def creer_profil(
    data: AcheteurCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ACHETEUR)),
):
    try:
        return acheteur_service.creer_profil(db, user, data)
    except AcheteurError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/mon-profil", response_model=AcheteurPublic)
def mon_profil(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ACHETEUR)),
):
    profil = acheteur_service.mon_profil(db, user)
    if profil is None:
        raise HTTPException(status_code=404, detail="Aucun profil acheteur")
    return profil


@router.get("/mon-eligibilite", response_model=EligibilitePublic)
def mon_eligibilite(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ACHETEUR)),
):
    return _elig_public(acheteur_service.eligibilite(db, user.id))


@router.get("/{user_id}/eligibilite", response_model=EligibilitePublic)
def eligibilite(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    return _elig_public(acheteur_service.eligibilite(db, user_id))


@router.post("/{user_id}/plafond", response_model=AcheteurPublic)
def definir_plafond(
    user_id: uuid.UUID,
    data: PlafondRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    try:
        return acheteur_service.definir_plafond(db, user_id, user, data.plafond_credit)
    except AcheteurError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
