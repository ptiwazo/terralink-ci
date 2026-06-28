"""Routes des transporteurs : profil, caution, validation OPS."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import Role, TransporteurStatut
from app.models.user import User
from app.schemas.livraison import CoursePublic
from app.schemas.transporteur import TransporteurCreate, TransporteurPublic
from app.services import livraison_service, transporteur_service
from app.services.transporteur_service import TransporteurError

router = APIRouter(prefix="/transporteurs", tags=["transporteurs"])


def _handle(exc: TransporteurError):
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/profil", response_model=TransporteurPublic, status_code=status.HTTP_201_CREATED)
def creer_profil(
    data: TransporteurCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.TRANSPORTEUR)),
):
    try:
        return transporteur_service.creer_profil(db, user, data)
    except TransporteurError as exc:
        _handle(exc)


@router.get("/mon-profil", response_model=TransporteurPublic)
def mon_profil(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.TRANSPORTEUR)),
):
    profil = transporteur_service.mon_profil(db, user)
    if profil is None:
        raise HTTPException(status_code=404, detail="Aucun profil transporteur")
    return profil


@router.get("/mes-courses", response_model=list[CoursePublic])
def mes_courses(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.TRANSPORTEUR)),
):
    courses = livraison_service.mes_courses(db, user)
    return [
        CoursePublic(
            livraison=liv,
            commande_id=cmd.id,
            commande_statut=cmd.statut.value,
            montant=cmd.montant_total,
            produits=", ".join(f"{l.quantite} × {l.produit.nom}" for l in cmd.lignes),
        )
        for liv, cmd in courses
    ]


@router.get("/valides", response_model=list[TransporteurPublic])
def lister_valides(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Transporteurs validés — utilisé par le producteur pour l'assignation."""
    return transporteur_service.lister(db, valides_seulement=True)


@router.get("", response_model=list[TransporteurPublic])
def lister_tous(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    return transporteur_service.lister(db)


@router.post("/{transporteur_id}/valider", response_model=TransporteurPublic)
def valider(
    transporteur_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    try:
        return transporteur_service.definir_statut(
            db, transporteur_id, user, TransporteurStatut.VALIDE
        )
    except TransporteurError as exc:
        _handle(exc)


@router.post("/{transporteur_id}/rejeter", response_model=TransporteurPublic)
def rejeter(
    transporteur_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    try:
        return transporteur_service.definir_statut(
            db, transporteur_id, user, TransporteurStatut.REJETE
        )
    except TransporteurError as exc:
        _handle(exc)
