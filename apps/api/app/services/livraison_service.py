"""Logique métier des livraisons (Phase 3).

Sécurité de la remise : à l'assignation d'un transporteur **validé**, un code de
remise est généré, **haché** en base (jamais en clair), et le clair n'est rendu
qu'une seule fois (à remettre au transporteur). La confirmation de réception par
l'acheteur n'aboutit QUE si le bon code est présenté — sinon la livraison ne peut
être confirmée et les fonds restent séquestrés.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import generer_code_remise, hash_code, verify_code
from app.models.commande import Commande
from app.models.enums import (
    CommandeStatut,
    LivraisonStatut,
    ModePaiement,
    Role,
    TransporteurStatut,
)
from app.models.livraison import Livraison
from app.models.transporteur import Transporteur
from app.models.user import User
from app.services import audit_service, escrow_service
from app.services.state_machine import TransitionError, verifier_et_cibler


class LivraisonError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_livraison(db: Session, commande_id: uuid.UUID) -> Livraison | None:
    return db.scalar(select(Livraison).where(Livraison.commande_id == commande_id))


def mes_courses(db: Session, user: User) -> list[tuple[Livraison, Commande]]:
    """Livraisons assignées au transporteur courant, avec leur commande."""
    transporteur = db.scalar(select(Transporteur).where(Transporteur.user_id == user.id))
    if transporteur is None:
        return []
    livraisons = db.scalars(
        select(Livraison)
        .where(Livraison.transporteur_id == transporteur.id)
        .order_by(Livraison.created_at.desc())
    )
    courses: list[tuple[Livraison, Commande]] = []
    for liv in livraisons:
        cmd = db.get(Commande, liv.commande_id)
        if cmd is not None:
            courses.append((liv, cmd))
    return courses


def _commande_du_producteur_ou_ops(commande: Commande, user: User) -> None:
    if user.role in (Role.OPS, Role.ADMIN):
        return
    if commande.producteur_id != user.id:
        raise LivraisonError("Seul le producteur de la commande peut agir", 403)


def assigner(
    db: Session, commande_id: uuid.UUID, transporteur_id: uuid.UUID, user: User
) -> tuple[Livraison, str]:
    """Assigne un transporteur validé et génère le code de remise.

    Renvoie (livraison, code_en_clair). Le clair n'est JAMAIS re-consultable
    ensuite (seul le hash est stocké)."""
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise LivraisonError("Commande introuvable", 404)
    _commande_du_producteur_ou_ops(commande, user)

    if commande.statut not in (CommandeStatut.PAYEE_SEQUESTRE, CommandeStatut.EN_PREPARATION):
        raise LivraisonError(
            "La commande doit être payée (séquestre) avant d'assigner un transporteur",
            409,
        )
    if get_livraison(db, commande_id) is not None:
        raise LivraisonError("Un transporteur est déjà assigné", 409)

    transporteur = db.get(Transporteur, transporteur_id)
    if transporteur is None:
        raise LivraisonError("Transporteur introuvable", 404)
    if transporteur.statut != TransporteurStatut.VALIDE:
        raise LivraisonError("Ce transporteur n'est pas validé", 409)

    code = generer_code_remise()
    livraison = Livraison(
        commande_id=commande_id,
        transporteur_id=transporteur_id,
        statut=LivraisonStatut.ASSIGNEE,
        code_remise_hash=hash_code(code),
        assurance_ref=f"ASSUR-{uuid.uuid4().hex[:8].upper()}",
        gps_traces=[],
    )
    db.add(livraison)
    db.flush()
    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action="LIVRAISON_ASSIGNEE",
        ressource_type="livraison",
        ressource_id=livraison.id,
        details={"transporteur_id": str(transporteur_id)},
    )
    db.commit()
    db.refresh(livraison)
    return livraison, code


def marquer_expediee_sans_commit(db: Session, commande: Commande) -> None:
    """Passe la livraison EN_COURS à l'expédition. NE COMMIT PAS (appelé par la
    transition EXPEDIER de la commande)."""
    livraison = get_livraison(db, commande.id)
    if livraison is None:
        raise LivraisonError("Assignez d'abord un transporteur", 409)
    if livraison.statut == LivraisonStatut.ASSIGNEE:
        livraison.statut = LivraisonStatut.EN_COURS


def ajouter_position(
    db: Session, commande_id: uuid.UUID, user: User, lat: float, lng: float
) -> Livraison:
    livraison = get_livraison(db, commande_id)
    if livraison is None:
        raise LivraisonError("Livraison introuvable", 404)
    transporteur = db.get(Transporteur, livraison.transporteur_id)
    if user.role not in (Role.OPS, Role.ADMIN) and (
        transporteur is None or transporteur.user_id != user.id
    ):
        raise LivraisonError("Seul le transporteur assigné peut tracer la position", 403)

    trace = {"lat": lat, "lng": lng, "ts": datetime.now(timezone.utc).isoformat()}
    # Réaffectation (et non mutation) pour que SQLAlchemy détecte le changement JSONB.
    livraison.gps_traces = list(livraison.gps_traces or []) + [trace]
    db.commit()
    db.refresh(livraison)
    return livraison


def noter_transporteur(
    db: Session, commande_id: uuid.UUID, user: User, note: int
) -> Livraison:
    """L'acheteur note le transporteur après livraison (1 à 5). Met à jour la
    note moyenne du transporteur."""
    if note < 1 or note > 5:
        raise LivraisonError("La note doit être comprise entre 1 et 5", 422)
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise LivraisonError("Commande introuvable", 404)
    if user.role not in (Role.OPS, Role.ADMIN) and commande.acheteur_id != user.id:
        raise LivraisonError("Seul l'acheteur peut noter le transporteur", 403)

    livraison = get_livraison(db, commande_id)
    if livraison is None or livraison.statut != LivraisonStatut.LIVREE:
        raise LivraisonError("La livraison n'est pas encore effectuée", 409)

    livraison.note_transporteur = note
    db.flush()

    # Recalcule la note moyenne du transporteur.
    moyenne = db.scalar(
        select(func.avg(Livraison.note_transporteur)).where(
            Livraison.transporteur_id == livraison.transporteur_id,
            Livraison.note_transporteur.isnot(None),
        )
    )
    transporteur = db.get(Transporteur, livraison.transporteur_id)
    if transporteur is not None and moyenne is not None:
        transporteur.note = round(float(moyenne), 2)

    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action="TRANSPORTEUR_NOTE",
        ressource_type="livraison",
        ressource_id=livraison.id,
        details={"note": note},
    )
    db.commit()
    db.refresh(livraison)
    return livraison


def confirmer_reception(
    db: Session, commande_id: uuid.UUID, user: User, code: str
) -> Commande:
    """Confirme la réception par l'acheteur, **uniquement avec le bon code**.
    Déclenche la libération des fonds (FONDS_LIBERES) dans la même transaction."""
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise LivraisonError("Commande introuvable", 404)
    livraison = get_livraison(db, commande_id)
    if livraison is None:
        raise LivraisonError("Aucune livraison pour cette commande", 404)

    # Valide rôle/propriété/statut via la machine à états (transition interne).
    try:
        cible = verifier_et_cibler(
            action="CONFIRMER_RECEPTION",
            statut_courant=commande.statut,
            role_acteur=user.role,
            acteur_id=user.id,
            acheteur_id=commande.acheteur_id,
            producteur_id=commande.producteur_id,
            interne=True,
        )
    except TransitionError as exc:
        raise LivraisonError(exc.message, exc.status_code)

    # LE garde-fou : code de remise correct exigé.
    if not verify_code(code, livraison.code_remise_hash):
        raise LivraisonError("Code de remise invalide", 403)

    commande.statut = cible  # LIVREE_CONFORME
    livraison.statut = LivraisonStatut.LIVREE
    livraison.livree_at = datetime.now(timezone.utc)
    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action="LIVRAISON_CONFIRMEE",
        ressource_type="commande",
        ressource_id=commande.id,
    )

    # COMPTANT : livraison conforme ⇒ libération des fonds séquestrés (même
    # transaction). DIFFERE : le producteur a déjà été payé d'avance ; la
    # commande reste LIVREE_CONFORME jusqu'au remboursement de la créance.
    if commande.mode_paiement == ModePaiement.COMPTANT:
        escrow_service.liberer_fonds_sans_commit(db, commande, user)
        commande.statut = CommandeStatut.FONDS_LIBERES
        audit_service.journaliser(
            db,
            acteur_id=user.id,
            action="COMMANDE_FONDS_LIBERES",
            ressource_type="commande",
            ressource_id=commande.id,
            details={"de": "LIVREE_CONFORME", "vers": "FONDS_LIBERES"},
        )
    db.commit()
    db.refresh(commande)
    return commande
