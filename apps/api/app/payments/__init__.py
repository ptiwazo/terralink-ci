"""Couche d'abstraction des paiements (CLAUDE.md §6).

`get_payment_provider()` renvoie l'implémentation active selon la config.
"""
from functools import lru_cache

from app.core.config import settings
from app.payments.base import PaymentProvider
from app.payments.mobile_money import MobileMoneyProvider
from app.payments.sandbox import SandboxProvider


@lru_cache
def get_payment_provider() -> PaymentProvider:
    if settings.payment_provider == "mobile_money":
        return MobileMoneyProvider()
    return SandboxProvider()


__all__ = ["PaymentProvider", "get_payment_provider"]
