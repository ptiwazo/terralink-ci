"""Catalogue de référence (lecture seule pour tous les utilisateurs connectés)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.produit import Produit
from app.models.user import User
from app.schemas.produit import ProduitPublic

router = APIRouter(prefix="/produits", tags=["produits"])


@router.get("", response_model=list[ProduitPublic])
def lister_produits(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Produit]:
    return list(
        db.scalars(select(Produit).where(Produit.actif).order_by(Produit.nom))
    )
