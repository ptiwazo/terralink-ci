"""`MobileMoneyProvider` — squelette pour Orange/MTN/Moov/Wave (CLAUDE.md §6).

⚠️ NE PAS inventer d'API réelle. Les appels HTTP vers l'agrégateur sont laissés
en TODO explicites. Les clés d'API viennent UNIQUEMENT de variables
d'environnement (jamais en dur).
"""
from app.payments.base import DepotInitie, PaiementEffectue, PaymentProvider


class MobileMoneyProvider(PaymentProvider):
    nom = "mobile_money"

    def initier_depot(self, *, montant: int, payeur: str, idempotency_key: str) -> DepotInitie:
        # TODO(mobile-money): appeler l'API de collecte de l'agrégateur.
        #   - URL/clé depuis settings (env), JAMAIS en dur.
        #   - passer `idempotency_key` au fournisseur (anti double-débit).
        #   - le fournisseur confirmera plus tard via webhook asynchrone signé
        #     (POST /api/v1/webhooks/paiement) — pas de confirmation immédiate.
        raise NotImplementedError("Intégration Mobile Money à brancher (voir TODO).")

    def effectuer_paiement(
        self, *, montant: int, beneficiaire: str, idempotency_key: str
    ) -> PaiementEffectue:
        # TODO(mobile-money): appeler l'API de payout (disbursement) de l'agrégateur.
        raise NotImplementedError("Payout Mobile Money à brancher (voir TODO).")

    def verifier_statut(self, ref_transaction: str) -> str:
        # TODO(mobile-money): GET statut transaction chez l'agrégateur.
        raise NotImplementedError
