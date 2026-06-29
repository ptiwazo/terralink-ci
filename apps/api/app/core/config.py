"""Configuration centralisée, chargée depuis l'environnement / .env.

Toutes les valeurs sensibles (secret JWT, URL de base) viennent de
l'environnement — jamais codées en dur (cf. CLAUDE.md §6, §9).
"""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normaliser_url_postgres(url: str) -> str:
    """Force le driver psycopg2. Les hébergeurs (Render/Railway/Heroku) fournissent
    une URL `postgres://` ou `postgresql://` que SQLAlchemy 2 n'accepte pas telle
    quelle ; on insère le driver attendu."""
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    return url


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

    # --- Compte admin initial (bootstrap au démarrage) ---
    # Si renseignés ET qu'aucun ADMIN/OPS n'existe encore, un compte est créé
    # au démarrage. Débloque l'accès OPS en prod sans shell.
    admin_telephone: str = ""
    admin_password: str = ""
    admin_nom: str = "Administrateur"
    admin_role: str = "ADMIN"

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

    # --- Suivi de livraison (ETA / approche) ---
    # Vitesse moyenne supposée pour l'estimation de l'heure d'arrivée (km/h).
    vitesse_livraison_kmh: float = 40.0
    # Distance (km) en deçà de laquelle on alerte « le véhicule approche ».
    seuil_approche_km: float = 2.0

    @model_validator(mode="after")
    def _fixer_drivers_db(self):
        self.database_url = _normaliser_url_postgres(self.database_url)
        self.test_database_url = _normaliser_url_postgres(self.test_database_url)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
