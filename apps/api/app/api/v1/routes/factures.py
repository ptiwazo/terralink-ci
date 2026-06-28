"""Routes de facturation (OHADA)."""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.commande import Commande
from app.models.enums import Role
from app.models.user import User
from app.schemas.facture import FacturePublic
from app.services import commande_service, facture_service
from app.services.commande_service import CommandeError
from app.services.facture_service import FactureError

router = APIRouter(tags=["factures"])


@router.post("/commandes/{commande_id}/facture", response_model=FacturePublic)
def emettre_facture(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    try:
        return facture_service.emettre(db, commande, user)
    except FactureError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/commandes/{commande_id}/facture", response_model=FacturePublic)
def detail_facture(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        commande_service.obtenir_commande(db, commande_id, user)  # contrôle d'accès
    except CommandeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    facture = facture_service.get_par_commande(db, commande_id)
    if facture is None:
        raise HTTPException(status_code=404, detail="Aucune facture")
    return facture


@router.get("/factures", response_model=list[FacturePublic])
def lister_factures(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.OPS, Role.ADMIN)),
):
    return facture_service.lister(db)


@router.get("/factures/{commande_id}/pdf")
def telecharger_pdf(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        commande_service.obtenir_commande(db, commande_id, user)
    except CommandeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    facture = facture_service.get_par_commande(db, commande_id)
    if facture is None or not facture.pdf_ref or not os.path.exists(facture.pdf_ref):
        raise HTTPException(status_code=404, detail="PDF introuvable")
    return FileResponse(
        facture.pdf_ref, media_type="application/pdf", filename=f"{facture.numero}.pdf"
    )
