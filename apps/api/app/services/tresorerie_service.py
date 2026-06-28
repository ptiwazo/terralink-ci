"""Trésorerie / paiement différé (CLAUDE.md §2.1, §4, Phase 4).

Flux (en partie double, solde global toujours 0) :
- Octroi d'avance (commande différée d'un acheteur éligible) :
    CREANCE:<acheteur> -M ; EXTERNE +montant_avance ; COMMISSION +commission ; DECOTE +decote
  Le producteur est payé immédiatement (montant_avance), une créance M est
  ouverte sur l'acheteur, commission + décote reconnues.
- Remboursement (à échéance) :
    CREANCE:<acheteur> +M ; EXTERNE -M
- Annulation de créance (résolution de litige en faveur de l'acheteur) :
    CREANCE +M ; COMMISSION -commission ; DECOTE -decote ; PERTES -montant_avance
  La plateforme absorbe l'avance versée (perte), la créance est éteinte.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.avance import AvanceTresorerie
from app.models.commande import Commande
from app.models.enums import AvanceStatut, CommandeStatut
from app.models.user import User
from app.payments import get_payment_provider
from app.services import audit_service, ledger_service


class TresorerieError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def calcul_avance(montant: int) -> tuple[int, int, int]:
    """Renvoie (commission, decote, montant_avance) en entiers FCFA."""
    commission = (montant * settings.commission_bps) // 10000
    decote = (montant * settings.decote_bps) // 10000
    return commission, decote, montant - commission - decote


def get_avance(db: Session, commande_id: uuid.UUID) -> AvanceTresorerie | None:
    return db.scalar(
        select(AvanceTresorerie).where(AvanceTresorerie.commande_id == commande_id)
    )


def octroyer_avance_sans_commit(db: Session, commande: Commande, acteur: User) -> AvanceTresorerie:
    """Verse l'avance au producteur et ouvre la créance acheteur. NE COMMIT PAS
    (appelé dans la transaction de création de commande différée)."""
    montant = commande.montant_total
    commission, decote, montant_avance = calcul_avance(montant)
    echeance = datetime.now(timezone.utc) + timedelta(days=settings.echeance_jours)
    compte_creance = ledger_service.compte_creance(commande.acheteur_id)
    compte_prod = ledger_service.compte_producteur(commande.producteur_id)

    avance = AvanceTresorerie(
        commande_id=commande.id,
        acheteur_id=commande.acheteur_id,
        montant=montant,
        montant_avance=montant_avance,
        commission=commission,
        decote=decote,
        echeance=echeance,
        statut=AvanceStatut.AVANCEE,
    )
    db.add(avance)

    # Paiement réel du producteur (sandbox/Mobile Money).
    provider = get_payment_provider()
    provider.effectuer_paiement(
        montant=montant_avance,
        beneficiaire=str(commande.producteur_id),
        idempotency_key=f"avance:{commande.id}",
    )

    ledger_service.poster(
        db,
        type="AVANCE_TRESORERIE",
        ref_idempotence=f"avance:{commande.id}",
        ref_commande=commande.id,
        legs=[
            (compte_creance, -montant, ledger_service.COMPTE_EXTERNE),
            (ledger_service.COMPTE_EXTERNE, montant_avance, compte_prod),
            (ledger_service.COMPTE_COMMISSION, commission, compte_creance),
            (ledger_service.COMPTE_DECOTE, decote, compte_creance),
        ],
    )
    commande.statut = CommandeStatut.AVANCE_VERSEE
    audit_service.journaliser(
        db,
        acteur_id=acteur.id,
        action="AVANCE_VERSEE",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"avance": montant_avance, "commission": commission, "decote": decote},
    )
    return avance


def rembourser_creance(db: Session, commande_id: uuid.UUID, user: User) -> AvanceTresorerie:
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise TresorerieError("Commande introuvable", 404)
    from app.models.enums import Role

    if user.role not in (Role.OPS, Role.ADMIN) and commande.acheteur_id != user.id:
        raise TresorerieError("Seul l'acheteur peut rembourser sa créance", 403)

    avance = get_avance(db, commande_id)
    if avance is None:
        raise TresorerieError("Aucune avance pour cette commande", 404)
    if avance.statut == AvanceStatut.REMBOURSEE:
        return avance  # idempotent
    if avance.statut not in (AvanceStatut.AVANCEE, AvanceStatut.IMPAYEE):
        raise TresorerieError("Créance non remboursable", 409)

    compte_creance = ledger_service.compte_creance(commande.acheteur_id)
    ledger_service.poster(
        db,
        type="REMBOURSEMENT_CREANCE",
        ref_idempotence=f"creance:{commande_id}",
        ref_commande=commande_id,
        legs=[
            (compte_creance, avance.montant, ledger_service.COMPTE_EXTERNE),
            (ledger_service.COMPTE_EXTERNE, -avance.montant, compte_creance),
        ],
    )
    avance.statut = AvanceStatut.REMBOURSEE
    if commande.statut == CommandeStatut.LIVREE_CONFORME:
        commande.statut = CommandeStatut.CLOTUREE
    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action="CREANCE_REMBOURSEE",
        ressource_type="commande",
        ressource_id=commande_id,
        details={"montant": avance.montant},
    )
    db.commit()
    db.refresh(avance)
    return avance


def annuler_creance_sans_commit(db: Session, commande: Commande, acteur: User) -> None:
    """Éteint la créance en faveur de l'acheteur (litige). NE COMMIT PAS.
    La plateforme absorbe l'avance déjà versée en perte."""
    avance = get_avance(db, commande.id)
    if avance is None:
        raise TresorerieError("Aucune avance pour cette commande", 409)
    if avance.statut == AvanceStatut.ANNULEE:
        return
    compte_creance = ledger_service.compte_creance(commande.acheteur_id)
    ledger_service.poster(
        db,
        type="ANNULATION_CREANCE",
        ref_idempotence=f"annul:{commande.id}",
        ref_commande=commande.id,
        legs=[
            (compte_creance, avance.montant, None),
            (ledger_service.COMPTE_COMMISSION, -avance.commission, compte_creance),
            (ledger_service.COMPTE_DECOTE, -avance.decote, compte_creance),
            (ledger_service.COMPTE_PERTES, -avance.montant_avance, compte_creance),
        ],
    )
    avance.statut = AvanceStatut.ANNULEE
    audit_service.journaliser(
        db,
        acteur_id=acteur.id,
        action="CREANCE_ANNULEE",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"perte": avance.montant_avance},
    )


def marquer_impayes(db: Session, acteur: User) -> int:
    """Bascule les avances échues non remboursées en IMPAYEE. Renvoie le nombre."""
    maintenant = datetime.now(timezone.utc)
    avances = list(
        db.scalars(
            select(AvanceTresorerie).where(
                AvanceTresorerie.statut == AvanceStatut.AVANCEE,
                AvanceTresorerie.echeance < maintenant,
            )
        )
    )
    for a in avances:
        a.statut = AvanceStatut.IMPAYEE
    if avances:
        audit_service.journaliser(
            db,
            acteur_id=acteur.id,
            action="IMPAYES_MARQUES",
            ressource_type="tresorerie",
            ressource_id=None,
            details={"nb": len(avances)},
        )
    db.commit()
    return len(avances)


def lister_impayes(db: Session) -> list[AvanceTresorerie]:
    return list(
        db.scalars(
            select(AvanceTresorerie)
            .where(AvanceTresorerie.statut == AvanceStatut.IMPAYEE)
            .order_by(AvanceTresorerie.echeance)
        )
    )
