"""Configuration centralisée, chargée depuis l'environnement / .env.

Toutes les valeurs sensibles (secret JWT, URL de base) viennent de
l'environnement — jamais codées en dur (cf. CLAUDE.md §6, §9).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Base de données
    database_url: str = "postgresql+psycopg2://terralink:terralink@localhost:5432/terralink"
    test_database_url: str = (
        "postgresql+psycopg2://terralink:terralink@localhost:5432/terralink_test"
    )

    # JWT
    jwt_secret: str = "dev-secret-a-changer-absolument-en-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS
    frontend_origin: str = "http://localhost:5173"

    # Environnement
    environment: str = "dev"

    # --- Paiement / Escrow (Phase 2) ---
    # Fournisseur de paiement actif : "sandbox" (dev/tests) ou "mobile_money".
    payment_provider: str = "sandbox"
    # Secret de signature des webhooks entrants (HMAC). À surcharger en prod.
    webhook_secret: str = "dev-webhook-secret-a-changer"
    # Commission de la plateforme en points de base (500 = 5,00 %). Entier.
    commission_bps: int = 500

    # --- Trésorerie / paiement différé (Phase 4) ---
    # Décote de financement prélevée sur l'avance producteur (200 = 2,00 %).
    decote_bps: int = 200
    # Délai de remboursement de la créance acheteur (jours, 30–60).
    echeance_jours: int = 45
    # Scoring : crédit accordé par commande comptant livrée, et plafond max.
    credit_unit_fcfa: int = 100000
    credit_max_fcfa: int = 5000000

    # --- Facturation / premium (Phase 5) ---
    # TVA des factures en points de base (0 = exonéré ; 1800 = 18 %).
    facture_tva_bps: int = 0
    # Abonnement premium : prix (FCFA) et durée (jours).
    premium_prix_fcfa: int = 25000
    premium_duree_jours: int = 30
    # Dossier de stockage des PDF de factures.
    factures_dir: str = "factures"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
