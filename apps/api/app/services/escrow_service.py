"""Service Escrow — cœur financier (CLAUDE.md §2.1, §6, Phase 2).

Cycle :
  1. `initier_depot`   : l'acheteur paie → dépôt initié (escrow EN_ATTENTE).
  2. `traiter_webhook` : confirmation signée du fournisseur → fonds séquestrés
     (ESCROW), commande → PAYEE_SEQUESTRE.
  3. `liberer_fonds`   : à LIVREE_CONFORME → commission prélevée + payout au
     producteur, escrow LIBERE, commande → FONDS_LIBERES.

Garde-fous :
- Montants en entiers FCFA, commission calculée serveur.
- Idempotence : clés d'idempotence + contrainte unique du grand livre.
- Double validation : le montant du webhook est comparé au montant recalculé.
- Atomicité : chaque opération valide ledger + statut dans UNE transaction.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.commande import Commande
from app.models.enums import CommandeStatut, EscrowStatut
from app.models.escrow import EscrowTransaction
from app.models.user import User
from app.payments import get_payment_provider
from app.payments.signature import signature_valide
from app.services import audit_service, ledger_service


class EscrowError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def calcul_commission(montant: int) -> tuple[int, int]:
    """Renvoie (commission, montant_net) en entiers FCFA. Commission arrondie
    à l'entier inférieur (le producteur n'est jamais lésé d'un arrondi vers le bas
    côté plateforme)."""
    commission = (montant * settings.commission_bps) // 10000
    return commission, montant - commission


def _cle_depot(commande_id: uuid.UUID) -> str:
    return f"depot:{commande_id}"


def get_escrow(db: Session, commande_id: uuid.UUID) -> EscrowTransaction | None:
    return db.scalar(
        select(EscrowTransaction).where(EscrowTransaction.commande_id == commande_id)
    )


def initier_depot(db: Session, commande: Commande, acteur: User) -> EscrowTransaction:
    if commande.acheteur_id != acteur.id:
        raise EscrowError("Seul l'acheteur peut payer cette commande", 403)

    # Idempotence : un seul séquestre par commande. Un second appel renvoie
    # l'escrow existant (quel que soit son statut), sans nouvelle écriture.
    existant = get_escrow(db, commande.id)
    if existant is not None:
        return existant

    if commande.statut != CommandeStatut.CREEE:
        raise EscrowError("La commande n'est pas en attente de paiement", 409)

    provider = get_payment_provider()
    cle = _cle_depot(commande.id)
    depot = provider.initier_depot(
        montant=commande.montant_total, payeur=str(acteur.id), idempotency_key=cle
    )

    escrow = EscrowTransaction(
        commande_id=commande.id,
        montant=commande.montant_total,
        statut=EscrowStatut.EN_ATTENTE,
        idempotency_key=cle,
        ref_depot=depot.ref_transaction,
    )
    db.add(escrow)
    audit_service.journaliser(
        db,
        acteur_id=acteur.id,
        action="ESCROW_DEPOT_INITIE",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"montant": commande.montant_total, "ref": depot.ref_transaction},
    )
    db.commit()
    db.refresh(escrow)

    # En sandbox, on rejoue immédiatement le webhook signé du fournisseur.
    if provider.confirme_automatiquement():
        evenement = provider.construire_evenement_depot(
            ref_transaction=depot.ref_transaction,
            montant=commande.montant_total,
            idempotency_key=cle,
        )
        traiter_webhook(db, evenement)
        db.refresh(escrow)

    return escrow


def traiter_webhook(db: Session, evenement: dict) -> EscrowTransaction:
    """Traite un webhook de confirmation de dépôt. Idempotent et signé."""
    if not signature_valide(evenement):
        raise EscrowError("Signature de webhook invalide", 401)

    cle = evenement.get("idempotency_key", "")
    escrow = db.scalar(
        select(EscrowTransaction).where(EscrowTransaction.idempotency_key == cle)
    )
    if escrow is None:
        raise EscrowError("Séquestre introuvable pour cette transaction", 404)

    commande = db.get(Commande, escrow.commande_id)
    if commande is None:
        raise EscrowError("Commande introuvable", 404)

    # Double validation du montant : on recompare au montant attendu (serveur).
    montant_recu = evenement.get("montant")
    if montant_recu != commande.montant_total:
        raise EscrowError(
            f"Montant incohérent : reçu {montant_recu}, attendu {commande.montant_total}",
            422,
        )

    # Idempotence : déjà traité → no-op.
    if escrow.statut != EscrowStatut.EN_ATTENTE:
        return escrow
    if commande.statut != CommandeStatut.CREEE:
        return escrow

    # Écriture du dépôt séquestré : EXTERNE -> ESCROW.
    ledger_service.poster(
        db,
        type="DEPOT_SEQUESTRE",
        ref_idempotence=_cle_depot(commande.id),
        ref_commande=commande.id,
        legs=[
            (ledger_service.COMPTE_ESCROW, escrow.montant, ledger_service.COMPTE_EXTERNE),
            (ledger_service.COMPTE_EXTERNE, -escrow.montant, ledger_service.COMPTE_ESCROW),
        ],
    )
    escrow.statut = EscrowStatut.SEQUESTRE
    commande.statut = CommandeStatut.PAYEE_SEQUESTRE
    audit_service.journaliser(
        db,
        acteur_id=None,
        action="ESCROW_SEQUESTRE",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"montant": escrow.montant},
    )
    db.commit()
    db.refresh(escrow)
    return escrow


def liberer_fonds_sans_commit(db: Session, commande: Commande, acteur: User) -> None:
    """Libère les fonds au producteur. NE COMMIT PAS et NE FIXE PAS le statut de
    la commande : le caller (confirmation de réception ou résolution de litige)
    pose le statut final dans la même transaction."""
    escrow = get_escrow(db, commande.id)
    if escrow is None:
        raise EscrowError("Aucun séquestre pour cette commande", 409)
    # Idempotence : déjà libéré → no-op.
    if escrow.statut == EscrowStatut.LIBERE:
        return
    if escrow.statut != EscrowStatut.SEQUESTRE:
        raise EscrowError("Les fonds ne sont pas séquestrés", 409)

    commission, net = calcul_commission(escrow.montant)
    compte_prod = ledger_service.compte_producteur(commande.producteur_id)

    # Répartition du séquestre : ESCROW -> COMMISSION + PRODUCTEUR.
    ledger_service.poster(
        db,
        type="LIBERATION",
        ref_idempotence=f"release:{commande.id}",
        ref_commande=commande.id,
        legs=[
            (ledger_service.COMPTE_ESCROW, -escrow.montant, None),
            (ledger_service.COMPTE_COMMISSION, commission, ledger_service.COMPTE_ESCROW),
            (compte_prod, net, ledger_service.COMPTE_ESCROW),
        ],
    )

    # Payout au producteur : PRODUCTEUR -> EXTERNE.
    provider = get_payment_provider()
    paiement = provider.effectuer_paiement(
        montant=net,
        beneficiaire=str(commande.producteur_id),
        idempotency_key=f"payout:{commande.id}",
    )
    ledger_service.poster(
        db,
        type="PAIEMENT_PRODUCTEUR",
        ref_idempotence=f"payout:{commande.id}",
        ref_commande=commande.id,
        legs=[
            (compte_prod, -net, ledger_service.COMPTE_EXTERNE),
            (ledger_service.COMPTE_EXTERNE, net, compte_prod),
        ],
    )

    escrow.statut = EscrowStatut.LIBERE
    escrow.commission = commission
    escrow.montant_net = net
    escrow.ref_paiement = paiement.ref_transaction
    audit_service.journaliser(
        db,
        acteur_id=acteur.id,
        action="ESCROW_LIBERE",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"commission": commission, "net": net},
    )


def rembourser_sans_commit(db: Session, commande: Commande, acteur: User) -> None:
    """Rembourse l'acheteur (résolution de litige). NE COMMIT PAS.

    Les fonds séquestrés repartent vers l'extérieur (acheteur). Aucun payout
    producteur, aucune commission."""
    escrow = get_escrow(db, commande.id)
    if escrow is None:
        raise EscrowError("Aucun séquestre pour cette commande", 409)
    if escrow.statut == EscrowStatut.REMBOURSE:
        return
    if escrow.statut != EscrowStatut.SEQUESTRE:
        raise EscrowError("Les fonds ne sont pas séquestrés", 409)

    # ESCROW -> EXTERNE (retour à l'acheteur).
    ledger_service.poster(
        db,
        type="REMBOURSEMENT",
        ref_idempotence=f"refund:{commande.id}",
        ref_commande=commande.id,
        legs=[
            (ledger_service.COMPTE_ESCROW, -escrow.montant, ledger_service.COMPTE_EXTERNE),
            (ledger_service.COMPTE_EXTERNE, escrow.montant, ledger_service.COMPTE_ESCROW),
        ],
    )
    escrow.statut = EscrowStatut.REMBOURSE
    audit_service.journaliser(
        db,
        acteur_id=acteur.id,
        action="ESCROW_REMBOURSE",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"montant": escrow.montant},
    )
