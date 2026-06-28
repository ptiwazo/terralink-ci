"""Routes prévisions de récolte et KPIs de pilotage."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import Role
from app.models.user import User
from app.services import analytics_service

router = APIRouter(tags=["analytics"])


@router.get("/previsions")
def previsions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    return analytics_service.previsions_recolte(db)


@router.get("/kpis")
def kpis(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
) -> dict:
    return analytics_service.kpis(db)
