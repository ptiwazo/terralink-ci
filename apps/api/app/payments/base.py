"""Interface `PaymentProvider` (CLAUDE.md §6).

Aucune logique de solde ici : un provider ne fait que dialoguer avec le monde
extérieur (dépôt, payout, statut) et émettre des événements de confirmation.
Toute la comptabilité reste côté serveur (ledger/escrow).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DepotInitie:
    ref_transaction: str
    statut: str  # "EN_ATTENTE" | "CONFIRME"


@dataclass(frozen=True)
class PaiementEffectue:
    ref_transaction: str
    statut: str  # "CONFIRME" | "EN_ATTENTE"


class PaymentProvider(ABC):
    """Contrat minimal d'un fournisseur de paiement."""

    nom: str

    @abstractmethod
    def initier_depot(
        self, *, montant: int, payeur: str, idempotency_key: str
    ) -> DepotInitie:
        """Initie un dépôt (l'acheteur paie la plateforme). Montant en FCFA."""

    @abstractmethod
    def effectuer_paiement(
        self, *, montant: int, beneficiaire: str, idempotency_key: str
    ) -> PaiementEffectue:
        """Effectue un payout (la plateforme paie le producteur/transporteur)."""

    @abstractmethod
    def verifier_statut(self, ref_transaction: str) -> str:
        """Renvoie le statut d'une transaction côté fournisseur."""

    def confirme_automatiquement(self) -> bool:
        """True si le dépôt est confirmé immédiatement (sandbox), sans attendre
        un vrai webhook asynchrone."""
        return False

    def construire_evenement_depot(
        self, *, ref_transaction: str, montant: int, idempotency_key: str
    ) -> dict:
        """Construit (et signe) l'événement webhook de confirmation de dépôt.

        Utilisé par le sandbox pour simuler le rappel du fournisseur, et par les
        tests. Un vrai fournisseur enverrait ce payload lui-même.
        """
        raise NotImplementedError
