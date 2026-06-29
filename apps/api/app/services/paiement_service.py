"""Historique des paiements reçus par un producteur (section « Mes paiements »).

Un producteur est payé de deux façons :
- **Escrow** (commande comptant) : à la livraison conforme, il reçoit le montant
  net (montant − commission). Source : `escrow_transactions` (statut LIBERE).
- **Avance de trésorerie** (commande différée) : il est payé d'avance
  (montant − commission − décote). Source : `avances_tresorerie`.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.avance import AvanceTresorerie
from app.models.commande import Commande
from app.models.enums import EscrowStatut
from app.models.escrow import EscrowTransaction
from app.models.user import User


def _produits(commande: Commande) -> str:
    return ", ".join(f"{l.quantite} × {l.produit.nom}" for l in commande.lignes)


def paiements_producteur(db: Session, user: User) -> dict:
    commandes = (
        db.scalars(select(Commande).where(Commande.producteur_id == user.id))
        .unique()
        .all()
    )
    items: list[dict] = []
    total = 0

    for cmd in commandes:
        escrow = db.scalar(
            select(EscrowTransaction).where(
                EscrowTransaction.commande_id == cmd.id,
                EscrowTransaction.statut == EscrowStatut.LIBERE,
            )
        )
        if escrow is not None:
            items.append(
                {
                    "commande_id": str(cmd.id),
                    "type": "ESCROW",
                    "montant": escrow.montant_net,
                    "statut": "VERSE",
                    "date": escrow.updated_at.isoformat() if escrow.updated_at else None,
                    "produits": _produits(cmd),
                }
            )
            total += escrow.montant_net

        avance = db.scalar(
            select(AvanceTresorerie).where(AvanceTresorerie.commande_id == cmd.id)
        )
        if avance is not None:
            items.append(
                {
                    "commande_id": str(cmd.id),
                    "type": "AVANCE",
                    "montant": avance.montant_avance,
                    "statut": avance.statut.value,
                    "date": avance.created_at.isoformat() if avance.created_at else None,
                    "produits": _produits(cmd),
                }
            )
            total += avance.montant_avance

    items.sort(key=lambda x: x["date"] or "", reverse=True)
    return {"total_recu": total, "nb": len(items), "paiements": items}
