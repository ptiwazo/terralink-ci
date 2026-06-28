"""Prévisions de récolte et KPIs de pilotage (CLAUDE.md §7, Phase 5)."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.avance import AvanceTresorerie
from app.models.commande import Commande
from app.models.enums import AvanceStatut, CommandeStatut, OffreStatut
from app.models.offre import Offre
from app.models.produit import Produit
from app.services import ledger_service

# Commandes dont la vente est réalisée (pour le GMV).
_REALISEES = (
    CommandeStatut.LIVREE_CONFORME,
    CommandeStatut.FONDS_LIBERES,
    CommandeStatut.CLOTUREE,
    CommandeStatut.RESOLUE_LIBEREE,
)
_LITIGES = (
    CommandeStatut.LITIGE,
    CommandeStatut.RESOLUE_REMBOURSEE,
    CommandeStatut.RESOLUE_LIBEREE,
)


def previsions_recolte(db: Session) -> list[dict]:
    """Agrégation des offres à venir (disponibles, dispo_le >= aujourd'hui)."""
    aujourdhui = date.today()
    rows = db.execute(
        select(
            Produit.nom,
            Produit.unite,
            func.sum(Offre.quantite_disponible),
            func.count(Offre.id),
        )
        .join(Produit, Produit.id == Offre.produit_id)
        .where(Offre.statut == OffreStatut.DISPONIBLE, Offre.dispo_le >= aujourdhui)
        .group_by(Produit.nom, Produit.unite)
        .order_by(func.sum(Offre.quantite_disponible).desc())
    ).all()
    return [
        {"produit": nom, "unite": unite.value if hasattr(unite, "value") else unite,
         "quantite_totale": int(qte or 0), "nb_offres": int(nb)}
        for nom, unite, qte, nb in rows
    ]


def kpis(db: Session) -> dict:
    nb_commandes = int(db.scalar(select(func.count(Commande.id))) or 0)
    gmv = int(
        db.scalar(
            select(func.coalesce(func.sum(Commande.montant_total), 0)).where(
                Commande.statut.in_(_REALISEES)
            )
        )
        or 0
    )

    par_statut = {
        statut.value: int(nb)
        for statut, nb in db.execute(
            select(Commande.statut, func.count(Commande.id)).group_by(Commande.statut)
        ).all()
    }

    nb_litiges = int(
        db.scalar(
            select(func.count(Commande.id)).where(Commande.statut.in_(_LITIGES))
        )
        or 0
    )
    sinistralite = round(nb_litiges / nb_commandes, 4) if nb_commandes else 0.0

    impayes_nb = int(
        db.scalar(
            select(func.count(AvanceTresorerie.id)).where(
                AvanceTresorerie.statut == AvanceStatut.IMPAYEE
            )
        )
        or 0
    )
    impayes_montant = int(
        db.scalar(
            select(func.coalesce(func.sum(AvanceTresorerie.montant), 0)).where(
                AvanceTresorerie.statut == AvanceStatut.IMPAYEE
            )
        )
        or 0
    )

    # Rétention : part d'acheteurs ayant passé au moins 2 commandes.
    sous = (
        select(Commande.acheteur_id, func.count(Commande.id).label("n"))
        .group_by(Commande.acheteur_id)
        .subquery()
    )
    nb_acheteurs = int(db.scalar(select(func.count()).select_from(sous)) or 0)
    nb_fideles = int(
        db.scalar(select(func.count()).select_from(sous).where(sous.c.n >= 2)) or 0
    )
    retention = round(nb_fideles / nb_acheteurs, 4) if nb_acheteurs else 0.0

    return {
        "gmv": gmv,
        "nb_commandes": nb_commandes,
        "par_statut": par_statut,
        "nb_litiges": nb_litiges,
        "sinistralite": sinistralite,
        "impayes_nb": impayes_nb,
        "impayes_montant": impayes_montant,
        "nb_acheteurs": nb_acheteurs,
        "retention": retention,
        "revenus": {
            "commission": ledger_service.solde(db, ledger_service.COMPTE_COMMISSION),
            "decote": ledger_service.solde(db, ledger_service.COMPTE_DECOTE),
            "abonnement": ledger_service.solde(db, ledger_service.COMPTE_ABONNEMENT),
            "pertes": ledger_service.solde(db, ledger_service.COMPTE_PERTES),
        },
    }
