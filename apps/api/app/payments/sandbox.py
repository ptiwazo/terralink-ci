"""`SandboxProvider` — simule dépôts et payouts en local (CLAUDE.md §6).

Tout réussit immédiatement. Le dépôt est « confirmé automatiquement » : on
fournit l'événement webhook signé pour rejouer le rappel du fournisseur, ce qui
permet de tester tout le chemin dépôt → webhook → séquestre sans agrégateur réel.
"""
import uuid

from app.payments.base import DepotInitie, PaiementEffectue, PaymentProvider
from app.payments.signature import signer


class SandboxProvider(PaymentProvider):
    nom = "sandbox"

    def initier_depot(self, *, montant: int, payeur: str, idempotency_key: str) -> DepotInitie:
        return DepotInitie(ref_transaction=f"sbx-dep-{uuid.uuid4().hex[:12]}", statut="EN_ATTENTE")

    def effectuer_paiement(
        self, *, montant: int, beneficiaire: str, idempotency_key: str
    ) -> PaiementEffectue:
        # En sandbox, le payout est confirmé immédiatement.
        return PaiementEffectue(ref_transaction=f"sbx-pay-{uuid.uuid4().hex[:12]}", statut="CONFIRME")

    def verifier_statut(self, ref_transaction: str) -> str:
        return "CONFIRME"

    def confirme_automatiquement(self) -> bool:
        return True

    def construire_evenement_depot(
        self, *, ref_transaction: str, montant: int, idempotency_key: str
    ) -> dict:
        evenement = {
            "type": "depot.confirme",
            "ref_transaction": ref_transaction,
            "idempotency_key": idempotency_key,
            "montant": montant,
        }
        evenement["signature"] = signer(evenement)
        return evenement
