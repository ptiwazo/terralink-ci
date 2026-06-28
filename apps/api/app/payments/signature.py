"""Signature HMAC des webhooks de paiement (CLAUDE.md §6).

Un webhook entrant est authentifié par signature (pas de JWT) : on recalcule
le HMAC-SHA256 sur le corps canonique et on compare en temps constant.
"""
import hashlib
import hmac
import json

from app.core.config import settings


def _corps_canonique(payload: dict) -> bytes:
    """Sérialisation déterministe du payload SANS le champ `signature`."""
    sans_sig = {k: v for k, v in payload.items() if k != "signature"}
    return json.dumps(sans_sig, sort_keys=True, separators=(",", ":")).encode("utf-8")


def signer(payload: dict) -> str:
    return hmac.new(
        settings.webhook_secret.encode("utf-8"),
        _corps_canonique(payload),
        hashlib.sha256,
    ).hexdigest()


def signature_valide(payload: dict) -> bool:
    fournie = payload.get("signature", "")
    attendue = signer(payload)
    return hmac.compare_digest(fournie, attendue)
