import pytest
import uuid
from sqlalchemy import text
from sqlalchemy.exc import InternalError
from fintech_ledger.models import Account, JournalEntry
from fintech_ledger.outbox_transfer import execute_transfer_outbox

def test_ledger_is_append_only(db_session):
    """Demuestra que la base de datos bloquea cualquier intento de modificar el dinero."""
    acc1 = Account(name="A", account_type="ASSET")
    acc2 = Account(name="B", account_type="ASSET")
    db_session.add(acc1)
    db_session.add(acc2)
    db_session.commit()

    tx_id = uuid.uuid4()
    execute_transfer_outbox(db_session, acc1.id, acc2.id, 100.00, tx_id)

    # Intentar modificar un asiento contable (SINTAXIS MALICIOSA)
    with pytest.raises(InternalError, match="COMPLIANCE VIOLATION"):
        db_session.execute(
            text("UPDATE journal_entries SET amount = 999999 WHERE transaction_id = :tx"), 
            {"tx": str(tx_id)}
        )
    
    db_session.rollback()

    # Intentar borrar un asiento contable
    with pytest.raises(InternalError, match="COMPLIANCE VIOLATION"):
        db_session.execute(
            text("DELETE FROM journal_entries WHERE transaction_id = :tx"), 
            {"tx": str(tx_id)}
        )
        
    db_session.rollback()
    print("\n" + "="*70)
    print("SOX COMPLIANCE CONFIRMADO: Base de datos bloqueo UPDATE y DELETE.")
    print("El libro mayor es inmutable. A prueba de manipulaciones.")
    print("="*70 + "\n")
