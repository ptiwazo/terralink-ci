"""Profil acheteur + scoring / éligibilité au paiement différé (CLAUDE.md §4, §7).

Scoring simple : le plafond suggéré dépend de l'historique de commandes
**comptant** menées à terme (statut FONDS_LIBERES). Le plafond effectif combine
ce scoring avec un éventuel plafond accordé manuellement par l'équipe OPS.
"""
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.acheteur import Acheteur
from app.models.avance import AvanceTresorerie
from app.models.commande import Commande
from app.models.enums import AvanceStatut, CommandeStatut, ModePaiement
from app.models.user import User
from app.schemas.acheteur import AcheteurCreate
from app.services import audit_service


class AcheteurError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class Eligibilite:
    score: int
    plafond_credit: int
    plafond_suggere: int
    plafond_effectif: int
    encours: int
    disponible: int


def creer_profil(db: Session, user: User, data: AcheteurCreate) -> Acheteur:
    if db.scalar(select(Acheteur).where(Acheteur.user_id == user.id)) is not None:
        raise AcheteurError("Profil acheteur déjà existant", 409)
    acheteur = Acheteur(user_id=user.id, type=data.type, adresse=data.adresse, plafond_credit=0)
    db.add(acheteur)
    db.flush()
    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action="ACHETEUR_PROFIL_CREE",
        ressource_type="acheteur",
        ressource_id=acheteur.id,
    )
    db.commit()
    db.refresh(acheteur)
    return acheteur


def mon_profil(db: Session, user: User) -> Acheteur | None:
    return db.scalar(select(Acheteur).where(Acheteur.user_id == user.id))


def get_par_user(db: Session, user_id: uuid.UUID) -> Acheteur:
    a = db.scalar(select(Acheteur).where(Acheteur.user_id == user_id))
    if a is None:
        raise AcheteurError("Profil acheteur introuvable", 404)
    return a


def definir_plafond(db: Session, user_id: uuid.UUID, acteur: User, plafond: int) -> Acheteur:
    acheteur = get_par_user(db, user_id)
    acheteur.plafond_credit = plafond
    audit_service.journaliser(
        db,
        acteur_id=acteur.id,
        action="ACHETEUR_PLAFOND_DEFINI",
        ressource_type="acheteur",
        ressource_id=acheteur.id,
        details={"plafond": plafond},
    )
    db.commit()
    db.refresh(acheteur)
    return acheteur


def _encours(db: Session, acheteur_user_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(AvanceTresorerie.montant), 0)).where(
                AvanceTresorerie.acheteur_id == acheteur_user_id,
                AvanceTresorerie.statut.in_(
                    [AvanceStatut.AVANCEE, AvanceStatut.IMPAYEE]
                ),
            )
        )
    )


def _score(db: Session, acheteur_user_id: uuid.UUID) -> int:
    """Nombre de commandes comptant menées à terme (FONDS_LIBERES)."""
    return int(
        db.scalar(
            select(func.count(Commande.id)).where(
                Commande.acheteur_id == acheteur_user_id,
                Commande.mode_paiement == ModePaiement.COMPTANT,
                Commande.statut == CommandeStatut.FONDS_LIBERES,
            )
        )
    )


def eligibilite(db: Session, acheteur_user_id: uuid.UUID) -> Eligibilite:
    profil = db.scalar(select(Acheteur).where(Acheteur.user_id == acheteur_user_id))
    plafond_manuel = profil.plafond_credit if profil else 0
    score = _score(db, acheteur_user_id)
    plafond_suggere = min(score * settings.credit_unit_fcfa, settings.credit_max_fcfa)
    plafond_effectif = max(plafond_manuel, plafond_suggere)
    encours = _encours(db, acheteur_user_id)
    return Eligibilite(
        score=score,
        plafond_credit=plafond_manuel,
        plafond_suggere=plafond_suggere,
        plafond_effectif=plafond_effectif,
        encours=encours,
        disponible=plafond_effectif - encours,
    )
