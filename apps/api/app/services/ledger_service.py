"""Service du grand livre en partie double (CLAUDE.md §2.1).

Règles dures :
- Toute écriture est **équilibrée** : la somme des montants signés vaut 0.
- Insertion seule (append-only) : ce module n'expose AUCUN update/delete.
- Les montants sont des **entiers FCFA**.

Le caller (escrow_service) ouvre/valide la transaction : `poster` ne fait
qu'ajouter les lignes à la session (pas de commit), pour rester atomique avec
le changement de statut de la commande/escrow.
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ledger import LedgerEntry

# --- Plan de comptes ---
COMPTE_ESCROW = "ESCROW"        # fonds séquestrés détenus par la plateforme
COMPTE_COMMISSION = "COMMISSION"  # revenu de la plateforme
COMPTE_EXTERNE = "EXTERNE"      # frontière avec le monde (Mobile Money / cash)


def compte_producteur(producteur_id: uuid.UUID) -> str:
    return f"PRODUCTEUR:{producteur_id}"


class LedgerError(Exception):
    pass


def poster(
    db: Session,
    *,
    type: str,
    ref_idempotence: str,
    legs: list[tuple[str, int, str | None]],
    ref_commande: uuid.UUID | None = None,
) -> None:
    """Insère une écriture équilibrée (plusieurs lignes) sans commit.

    `legs` : liste de (compte, montant_signé, contrepartie).
    Lève `LedgerError` si l'écriture n'est pas équilibrée.
    """
    if len(legs) < 2:
        raise LedgerError("Une écriture doit comporter au moins deux lignes")
    if sum(montant for _, montant, _ in legs) != 0:
        raise LedgerError("Écriture déséquilibrée : la somme des montants doit être nulle")

    for compte, montant, contrepartie in legs:
        db.add(
            LedgerEntry(
                compte=compte,
                contrepartie=contrepartie,
                montant=montant,
                type=type,
                ref_commande=ref_commande,
                ref_idempotence=ref_idempotence,
            )
        )


def solde(db: Session, compte: str) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(LedgerEntry.montant), 0)).where(
                LedgerEntry.compte == compte
            )
        )
    )


def solde_global(db: Session) -> int:
    """Somme de TOUS les montants du grand livre — doit toujours valoir 0
    (invariant « le solde ne fuit jamais »)."""
    return int(db.scalar(select(func.coalesce(func.sum(LedgerEntry.montant), 0))))
