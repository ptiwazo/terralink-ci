"""Logique métier des transporteurs : profil, caution, validation OPS."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TransporteurStatut
from app.models.transporteur import Transporteur
from app.models.user import User
from app.schemas.transporteur import TransporteurCreate
from app.services import audit_service


class TransporteurError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def creer_profil(db: Session, user: User, data: TransporteurCreate) -> Transporteur:
    existant = db.scalar(select(Transporteur).where(Transporteur.user_id == user.id))
    if existant is not None:
        raise TransporteurError("Profil transporteur déjà existant", 409)

    transporteur = Transporteur(
        user_id=user.id,
        vehicule=data.vehicule,
        immatriculation=data.immatriculation,
        caution_deposee=data.caution_deposee,
        statut=TransporteurStatut.EN_ATTENTE,
    )
    db.add(transporteur)
    db.flush()
    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action="TRANSPORTEUR_PROFIL_CREE",
        ressource_type="transporteur",
        ressource_id=transporteur.id,
        details={"caution": data.caution_deposee},
    )
    db.commit()
    db.refresh(transporteur)
    return transporteur


def mon_profil(db: Session, user: User) -> Transporteur | None:
    return db.scalar(select(Transporteur).where(Transporteur.user_id == user.id))


def get(db: Session, transporteur_id: uuid.UUID) -> Transporteur:
    t = db.get(Transporteur, transporteur_id)
    if t is None:
        raise TransporteurError("Transporteur introuvable", 404)
    return t


def lister(db: Session, valides_seulement: bool = False) -> list[Transporteur]:
    stmt = select(Transporteur).order_by(Transporteur.created_at.desc())
    if valides_seulement:
        stmt = stmt.where(Transporteur.statut == TransporteurStatut.VALIDE)
    return list(db.scalars(stmt))


def definir_statut(
    db: Session, transporteur_id: uuid.UUID, acteur: User, statut: TransporteurStatut
) -> Transporteur:
    transporteur = get(db, transporteur_id)
    transporteur.statut = statut
    audit_service.journaliser(
        db,
        acteur_id=acteur.id,
        action=f"TRANSPORTEUR_{statut.value}",
        ressource_type="transporteur",
        ressource_id=transporteur.id,
    )
    db.commit()
    db.refresh(transporteur)
    return transporteur
