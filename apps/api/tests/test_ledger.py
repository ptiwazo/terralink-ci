"""Tests unitaires du grand livre en partie double (CLAUDE.md §2.1)."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.services import ledger_service
from app.services.ledger_service import (
    COMPTE_ESCROW,
    COMPTE_EXTERNE,
    LedgerError,
)


def test_ecriture_equilibree_et_solde(db_session):
    ledger_service.poster(
        db_session,
        type="TEST",
        ref_idempotence="op:1",
        legs=[(COMPTE_ESCROW, 1000, COMPTE_EXTERNE), (COMPTE_EXTERNE, -1000, COMPTE_ESCROW)],
    )
    db_session.flush()
    assert ledger_service.solde(db_session, COMPTE_ESCROW) == 1000
    assert ledger_service.solde(db_session, COMPTE_EXTERNE) == -1000
    assert ledger_service.solde_global(db_session) == 0


def test_ecriture_desequilibree_refusee(db_session):
    with pytest.raises(LedgerError):
        ledger_service.poster(
            db_session,
            type="TEST",
            ref_idempotence="op:2",
            legs=[(COMPTE_ESCROW, 1000, None), (COMPTE_EXTERNE, -999, None)],
        )


def test_ecriture_une_seule_ligne_refusee(db_session):
    with pytest.raises(LedgerError):
        ledger_service.poster(
            db_session, type="TEST", ref_idempotence="op:3", legs=[(COMPTE_ESCROW, 0, None)]
        )


def test_double_passage_meme_operation_rejete(db_session):
    """Filet de sécurité d'idempotence : (ref_idempotence, compte) est unique."""
    legs = [(COMPTE_ESCROW, 500, COMPTE_EXTERNE), (COMPTE_EXTERNE, -500, COMPTE_ESCROW)]
    ledger_service.poster(db_session, type="TEST", ref_idempotence="op:4", legs=legs)
    db_session.flush()
    ledger_service.poster(db_session, type="TEST", ref_idempotence="op:4", legs=legs)
    with pytest.raises(IntegrityError):
        db_session.flush()
