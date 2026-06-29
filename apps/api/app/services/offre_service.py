"""Logique métier des offres (stocks) côté producteur.

Toute vérification d'appartenance est faite ici, côté serveur : un producteur
ne peut créer/modifier que SES offres (CLAUDE.md §2.2).
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import OffreStatut
from app.models.offre import Offre
from app.models.produit import Produit
from app.models.user import User
from app.schemas.offre import OffreCreate, OffreUpdate
from app.services import audit_service


class OffreError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _produit_actif(db: Session, produit_id: uuid.UUID) -> Produit:
    produit = db.get(Produit, produit_id)
    if produit is None or not produit.actif:
        raise OffreError("Produit inconnu ou inactif", 404)
    return produit


def creer_offre(db: Session, producteur: User, data: OffreCreate) -> Offre:
    _produit_actif(db, data.produit_id)
    offre = Offre(
        producteur_id=producteur.id,
        produit_id=data.produit_id,
        quantite_disponible=data.quantite_disponible,
        prix_unitaire=data.prix_unitaire,
        qualite=data.qualite,
        dispo_le=data.dispo_le,
        ville=data.ville,
        lat=data.lat,
        lng=data.lng,
        statut=OffreStatut.DISPONIBLE,
    )
    db.add(offre)
    db.flush()
    audit_service.journaliser(
        db,
        acteur_id=producteur.id,
        action="OFFRE_CREEE",
        ressource_type="offre",
        ressource_id=offre.id,
        details={"produit_id": str(data.produit_id), "prix": data.prix_unitaire},
    )
    db.commit()
    db.refresh(offre)
    return offre


def _charger_offre_du_producteur(
    db: Session, offre_id: uuid.UUID, producteur: User
) -> Offre:
    offre = db.get(Offre, offre_id)
    if offre is None:
        raise OffreError("Offre introuvable", 404)
    if offre.producteur_id != producteur.id:
        raise OffreError("Cette offre ne vous appartient pas", 403)
    return offre


def maj_offre(
    db: Session, offre_id: uuid.UUID, producteur: User, data: OffreUpdate
) -> Offre:
    offre = _charger_offre_du_producteur(db, offre_id, producteur)
    champs = data.model_dump(exclude_unset=True)
    for k, v in champs.items():
        setattr(offre, k, v)
    # Cohérence statut/stock
    if offre.quantite_disponible <= 0 and offre.statut == OffreStatut.DISPONIBLE:
        offre.statut = OffreStatut.EPUISEE
    audit_service.journaliser(
        db,
        acteur_id=producteur.id,
        action="OFFRE_MODIFIEE",
        ressource_type="offre",
        ressource_id=offre.id,
        details={k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in champs.items()},
    )
    db.commit()
    db.refresh(offre)
    return offre


def retirer_offre(db: Session, offre_id: uuid.UUID, producteur: User) -> Offre:
    """Retrait logique (statut RETIREE) — on conserve l'historique."""
    offre = _charger_offre_du_producteur(db, offre_id, producteur)
    offre.statut = OffreStatut.RETIREE
    audit_service.journaliser(
        db,
        acteur_id=producteur.id,
        action="OFFRE_RETIREE",
        ressource_type="offre",
        ressource_id=offre.id,
    )
    db.commit()
    db.refresh(offre)
    return offre


def lister_mes_offres(db: Session, producteur: User) -> list[Offre]:
    return list(
        db.scalars(
            select(Offre)
            .where(Offre.producteur_id == producteur.id)
            .order_by(Offre.created_at.desc())
        )
    )


def obtenir_offre(db: Session, offre_id: uuid.UUID) -> Offre:
    offre = db.get(Offre, offre_id)
    if offre is None:
        raise OffreError("Offre introuvable", 404)
    return offre
