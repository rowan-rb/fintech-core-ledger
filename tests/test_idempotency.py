import pytest
import uuid
from fintech_ledger.idempotent_worker import process_transfer_event, DuplicateTransactionError
from fintech_ledger.models import JournalEntry, Account

def test_idempotency_prevents_double_charging(db_session):
    """Demuestra que un mensaje duplicado no mueve el dinero dos veces."""
    acc1 = Account(name="Cuenta A", account_type="ASSET")
    acc2 = Account(name="Cuenta B", account_type="ASSET")
    db_session.add(acc1)
    db_session.add(acc2)
    db_session.commit()

    tx_id = uuid.uuid4()
    
    # 1. Procesamos por primera vez (debe funcionar)
    result = process_transfer_event(db_session, tx_id, acc1.id, acc2.id, 100.00)
    assert result is True
    
    # Verificamos que el dinero se movió (2 asientos)
    count = db_session.query(JournalEntry).filter(JournalEntry.transaction_id == tx_id).count()
    assert count == 2

    # 2. El broker reenvía el mensaje por un fallo de red. Intentamos procesar de nuevo.
    with pytest.raises(DuplicateTransactionError):
        process_transfer_event(db_session, tx_id, acc1.id, acc2.id, 100.00)

    # 3. El broker falla otra vez y lo reenvía una tercera vez.
    with pytest.raises(DuplicateTransactionError):
        process_transfer_event(db_session, tx_id, acc1.id, acc2.id, 100.00)

    # VERIFICACIÓN: A pesar de intentarlo 3 veces, solo hay 2 asientos.
    # ¡El usuario NO ha sido cobrado dos veces!
    final_count = db_session.query(JournalEntry).filter(JournalEntry.transaction_id == tx_id).count()
    assert final_count == 2

    print("\n" + "="*70)
    print("IDEMPOTENCIA CONFIRMADA: Mensaje duplicado 3 veces.")
    print("El usuario solo ha sido cobrado UNA vez. Integridad financiera protegida.")
    print("="*70 + "\n")
