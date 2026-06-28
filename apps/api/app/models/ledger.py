"""Grand livre en partie double — `ledger_entries` (CLAUDE.md §2.1, §4).

**APPEND-ONLY** : aucune ligne n'est jamais modifiée ou supprimée. Les
corrections se font par écriture inverse. C'est la base de l'auditabilité.

Chaque opération financière insère plusieurs lignes (legs) dont la somme des
`montant` (signés, en entiers FCFA) vaut exactement 0. Le solde d'un compte
est la somme de ses `montant`.

`ref_idempotence` identifie l'opération métier (ex: `depot:<commande>`). La
contrainte d'unicité (ref_idempotence, compte) empêche tout double-passage
d'une même opération — filet de sécurité de l'idempotence.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint("ref_idempotence", "compte", name="uq_ledger_idem_compte"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    compte: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    contrepartie: Mapped[str | None] = mapped_column(String(80), nullable=True)
    montant: Mapped[int] = mapped_column(BigInteger, nullable=False)  # signé, FCFA
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    ref_commande: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    ref_idempotence: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
