"""Abonnements premium (CLAUDE.md §4, Phase 5)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.abonnement import AbonnementPremium
from app.models.enums import AbonnementFormule, AbonnementStatut
from app.models.user import User
from app.services import audit_service, ledger_service


class PremiumError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def abonnement_actif(db: Session, user_id) -> AbonnementPremium | None:
    maintenant = datetime.now(timezone.utc)
    return db.scalar(
        select(AbonnementPremium)
        .where(
            AbonnementPremium.acheteur_id == user_id,
            AbonnementPremium.statut == AbonnementStatut.ACTIF,
            AbonnementPremium.fin > maintenant,
        )
        .order_by(AbonnementPremium.fin.desc())
    )


def souscrire(db: Session, user: User, formule: AbonnementFormule) -> AbonnementPremium:
    existant = abonnement_actif(db, user.id)
    if existant is not None:
        return existant  # déjà abonné : idempotent sur la période en cours

    debut = datetime.now(timezone.utc)
    fin = debut + timedelta(days=settings.premium_duree_jours)
    prix = settings.premium_prix_fcfa if formule == AbonnementFormule.PREMIUM else 0

    abo = AbonnementPremium(
        acheteur_id=user.id,
        formule=formule,
        debut=debut,
        fin=fin,
        prix=prix,
        statut=AbonnementStatut.ACTIF,
    )
    db.add(abo)
    db.flush()

    if prix > 0:
        # Paiement de l'abonnement : EXTERNE -> ABONNEMENT (revenu).
        ledger_service.poster(
            db,
            type="ABONNEMENT_PREMIUM",
            ref_idempotence=f"abo:{abo.id}",
            legs=[
                (ledger_service.COMPTE_ABONNEMENT, prix, ledger_service.COMPTE_EXTERNE),
                (ledger_service.COMPTE_EXTERNE, -prix, ledger_service.COMPTE_ABONNEMENT),
            ],
        )

    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action="PREMIUM_SOUSCRIT",
        ressource_type="abonnement",
        ressource_id=abo.id,
        details={"formule": formule.value, "prix": prix},
    )
    db.commit()
    db.refresh(abo)
    return abo


def mon_abonnement(db: Session, user: User) -> AbonnementPremium | None:
    return db.scalar(
        select(AbonnementPremium)
        .where(AbonnementPremium.acheteur_id == user.id)
        .order_by(AbonnementPremium.created_at.desc())
    )
