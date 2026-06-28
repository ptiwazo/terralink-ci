"""Logique métier des commandes (Phase 1, sans argent réel).

Points non négociables respectés :
- `montant_total` recalculé **côté serveur** à partir des prix en base (jamais
  reçu du client) — CLAUDE.md §2.1.
- Création atomique : verrouillage des offres (`FOR UPDATE`), décrément du
  stock et insertion de la commande dans **une seule transaction** ; en cas
  d'erreur, rollback total (pas d'état incohérent) — CLAUDE.md §2.1.
- Une commande = un seul producteur.
- Transitions via la machine à états explicite — CLAUDE.md §5.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, lazyload

from app.models.commande import Commande, LigneCommande
from app.models.enums import CommandeStatut, OffreStatut, Role
from app.models.offre import Offre
from app.models.user import User
from app.schemas.commande import CommandeCreate
from app.services import audit_service, escrow_service, livraison_service
from app.services.state_machine import TransitionError, verifier_et_cibler


class CommandeError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def creer_commande(db: Session, acheteur: User, data: CommandeCreate) -> Commande:
    if not data.lignes:
        raise CommandeError("La commande doit contenir au moins une ligne", 422)

    offre_ids = [l.offre_id for l in data.lignes]
    if len(set(offre_ids)) != len(offre_ids):
        raise CommandeError("Offre en double dans la commande", 422)

    # Verrou pessimiste sur les offres : empêche deux commandes concurrentes
    # de surconsommer le même stock. On désactive le chargement eager des
    # relations (sinon les OUTER JOIN rendent `FOR UPDATE` invalide sous Postgres).
    offres = {
        o.id: o
        for o in db.scalars(
            select(Offre)
            .where(Offre.id.in_(offre_ids))
            .options(lazyload(Offre.produit), lazyload(Offre.producteur))
            .with_for_update()
        )
    }

    producteur_id: uuid.UUID | None = None
    montant_total = 0
    lignes: list[LigneCommande] = []

    for ligne in data.lignes:
        offre = offres.get(ligne.offre_id)
        if offre is None:
            raise CommandeError(f"Offre introuvable : {ligne.offre_id}", 404)
        if offre.statut != OffreStatut.DISPONIBLE:
            raise CommandeError("Offre non disponible", 409)
        if ligne.quantite <= 0:
            raise CommandeError("Quantité invalide", 422)
        if ligne.quantite > offre.quantite_disponible:
            raise CommandeError(
                f"Stock insuffisant pour l'offre {offre.id} "
                f"(disponible : {offre.quantite_disponible})",
                409,
            )

        if producteur_id is None:
            producteur_id = offre.producteur_id
        elif offre.producteur_id != producteur_id:
            raise CommandeError(
                "Une commande ne peut concerner qu'un seul producteur", 422
            )

        # Montant calculé serveur, en entiers FCFA.
        montant_total += ligne.quantite * offre.prix_unitaire
        lignes.append(
            LigneCommande(
                offre_id=offre.id,
                produit_id=offre.produit_id,
                quantite=ligne.quantite,
                prix_unitaire=offre.prix_unitaire,  # snapshot
            )
        )

        # Décrément du stock + épuisement éventuel.
        offre.quantite_disponible -= ligne.quantite
        if offre.quantite_disponible == 0:
            offre.statut = OffreStatut.EPUISEE

    if acheteur.id == producteur_id:
        raise CommandeError("Vous ne pouvez pas commander vos propres offres", 422)

    commande = Commande(
        acheteur_id=acheteur.id,
        producteur_id=producteur_id,
        statut=CommandeStatut.CREEE,
        montant_total=montant_total,
        mode_paiement=data.mode_paiement,
        lignes=lignes,
    )
    db.add(commande)
    db.flush()
    audit_service.journaliser(
        db,
        acteur_id=acheteur.id,
        action="COMMANDE_CREEE",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"montant_total": montant_total, "nb_lignes": len(lignes)},
    )
    db.commit()
    db.refresh(commande)
    return commande


def _charger_visible(db: Session, commande_id: uuid.UUID, user: User) -> Commande:
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise CommandeError("Commande introuvable", 404)
    autorise = (
        user.role in (Role.OPS, Role.ADMIN)
        or commande.acheteur_id == user.id
        or commande.producteur_id == user.id
    )
    if not autorise:
        raise CommandeError("Accès refusé à cette commande", 403)
    return commande


def obtenir_commande(db: Session, commande_id: uuid.UUID, user: User) -> Commande:
    return _charger_visible(db, commande_id, user)


def lister_mes_commandes(db: Session, user: User) -> list[Commande]:
    stmt = select(Commande).order_by(Commande.created_at.desc())
    if user.role == Role.ACHETEUR:
        stmt = stmt.where(Commande.acheteur_id == user.id)
    elif user.role == Role.PRODUCTEUR:
        stmt = stmt.where(Commande.producteur_id == user.id)
    elif user.role in (Role.OPS, Role.ADMIN):
        pass  # voient tout
    else:
        return []
    # `.unique()` requis : `lignes` est une collection chargée en eager-join.
    return list(db.scalars(stmt).unique())


def appliquer_transition(
    db: Session, commande_id: uuid.UUID, user: User, action: str
) -> Commande:
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise CommandeError("Commande introuvable", 404)

    try:
        cible = verifier_et_cibler(
            action=action,
            statut_courant=commande.statut,
            role_acteur=user.role,
            acteur_id=user.id,
            acheteur_id=commande.acheteur_id,
            producteur_id=commande.producteur_id,
        )
    except TransitionError as exc:
        raise CommandeError(exc.message, exc.status_code)

    ancien = commande.statut
    commande.statut = cible
    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action=f"COMMANDE_{action}",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"de": ancien.value, "vers": cible.value},
    )

    # À l'expédition, la livraison (transporteur assigné) passe EN_COURS.
    if cible == CommandeStatut.EN_LIVRAISON:
        try:
            livraison_service.marquer_expediee_sans_commit(db, commande)
        except livraison_service.LivraisonError as exc:
            raise CommandeError(exc.message, exc.status_code)

    db.commit()
    db.refresh(commande)
    return commande


def resoudre_litige(db: Session, commande_id: uuid.UUID, user: User, sens: str) -> Commande:
    """Résout un litige (OPS/ADMIN) : remboursement acheteur ou libération
    producteur. Mouvement de fonds + statut final dans une seule transaction."""
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise CommandeError("Commande introuvable", 404)

    action = "RESOUDRE_REMBOURSEMENT" if sens == "REMBOURSE" else "RESOUDRE_LIBERATION"
    try:
        cible = verifier_et_cibler(
            action=action,
            statut_courant=commande.statut,
            role_acteur=user.role,
            acteur_id=user.id,
            acheteur_id=commande.acheteur_id,
            producteur_id=commande.producteur_id,
            interne=True,
        )
    except TransitionError as exc:
        raise CommandeError(exc.message, exc.status_code)

    if sens == "REMBOURSE":
        escrow_service.rembourser_sans_commit(db, commande, user)
    else:
        escrow_service.liberer_fonds_sans_commit(db, commande, user)

    commande.statut = cible
    audit_service.journaliser(
        db,
        acteur_id=user.id,
        action=f"COMMANDE_{action}",
        ressource_type="commande",
        ressource_id=commande.id,
        details={"sens": sens, "vers": cible.value},
    )
    db.commit()
    db.refresh(commande)
    return commande
