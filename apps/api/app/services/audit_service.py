"""Écriture du journal d'audit (CLAUDE.md §2.3).

`journaliser` ajoute une ligne à la session courante SANS commit : l'audit
fait partie de la même transaction que l'action auditée (tout-ou-rien).
"""
import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def journaliser(
    db: Session,
    *,
    acteur_id: uuid.UUID | None,
    action: str,
    ressource_type: str,
    ressource_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            acteur_id=acteur_id,
            action=action,
            ressource_type=ressource_type,
            ressource_id=ressource_id,
            details=details,
        )
    )
