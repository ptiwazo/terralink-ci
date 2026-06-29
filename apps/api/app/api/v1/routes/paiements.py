"""Routes de paiement / escrow (Phase 2).

- POST /commandes/{id}/payer : l'acheteur initie le dépôt séquestré.
- GET  /commandes/{id}/escrow : état du séquestre (parties prenantes).
- POST /webhooks/paiement : rappel du fournisseur (authentifié par SIGNATURE,
  pas par JWT — exception machine-à-machine documentée, cf. §2.2/§6).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.escrow import EscrowPublic, WebhookPaiement
from app.services import commande_service, escrow_service, paiement_service
from app.services.commande_service import CommandeError
from app.services.escrow_service import EscrowError

router = APIRouter(tags=["paiements"])


@router.get("/paiements/mes")
def mes_paiements(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.PRODUCTEUR)),
) -> dict:
    """Historique des paiements reçus par le producteur (escrow + avances)."""
    return paiement_service.paiements_producteur(db, user)


@router.post("/commandes/{commande_id}/payer", response_model=EscrowPublic)
def payer(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        commande = commande_service.obtenir_commande(db, commande_id, user)
        return escrow_service.initier_depot(db, commande, user)
    except (CommandeError, EscrowError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/commandes/{commande_id}/escrow", response_model=EscrowPublic)
def detail_escrow(
    commande_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        # Vérifie la visibilité de la commande (acheteur/producteur/ops).
        commande_service.obtenir_commande(db, commande_id, user)
    except CommandeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    escrow = escrow_service.get_escrow(db, commande_id)
    if escrow is None:
        raise HTTPException(status_code=404, detail="Aucun séquestre pour cette commande")
    return escrow


@router.post("/webhooks/paiement")
def webhook_paiement(evenement: WebhookPaiement, db: Session = Depends(get_db)):
    try:
        escrow = escrow_service.traiter_webhook(db, evenement.model_dump())
    except EscrowError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return {"status": "ok", "escrow_statut": escrow.statut.value}
