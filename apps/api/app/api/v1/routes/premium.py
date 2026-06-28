"""Routes des abonnements premium (acheteur)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.abonnement import AbonnementCreate, AbonnementPublic
from app.services import premium_service
from app.services.premium_service import PremiumError

router = APIRouter(prefix="/premium", tags=["premium"])


@router.post("/souscrire", response_model=AbonnementPublic)
def souscrire(
    data: AbonnementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ACHETEUR)),
):
    try:
        return premium_service.souscrire(db, user, data.formule)
    except PremiumError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/mon-abonnement", response_model=AbonnementPublic | None)
def mon_abonnement(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ACHETEUR)),
):
    return premium_service.mon_abonnement(db, user)
