import pytest
import uuid
from fintech_ledger.outbox_transfer import execute_transfer_outbox
from fintech_ledger.models import JournalEntry, Account, OutboxEvent

def test_outbox_prevents_money_loss(db_session):
    """Demuestra que el Outbox guarda el evento a salvo incluso si RabbitMQ cae."""
    acc1 = Account(name="Cuenta A", account_type="ASSET")
    acc2 = Account(name="Cuenta B", account_type="ASSET")
    db_session.add(acc1)
    db_session.add(acc2)
    db_session.commit()

    tx_id = uuid.uuid4()
    
    # Ejecutamos la transferencia con el patrón Outbox (sin RabbitMQ de por medio)
    event_id = execute_transfer_outbox(
        db_session, acc1.id, acc2.id, 5000.00, tx_id
    )

    # VERIFICACIÓN 1: Los asientos contables están en la BD
    journal_count = db_session.query(JournalEntry).filter(
        JournalEntry.transaction_id == tx_id
    ).count()
    assert journal_count == 2, "El dinero no se movió en la BD."

    # VERIFICACIÓN 2: El evento está a salvo en la tabla outbox esperando ser enviado
    outbox_event = db_session.query(OutboxEvent).filter(
        OutboxEvent.id == event_id
    ).first()
    
    assert outbox_event is not None, "El evento no se guardó en el Outbox."
    assert outbox_event.processed_at is None, "El evento no debería estar procesado aún."
    assert outbox_event.payload["amount"] == 5000.00

    print("\n" + "="*70)
    print("FIX CONFIRMADO: Dinero movido en BD Y evento guardado en Outbox.")
    print("Aunque RabbitMQ explote ahora, el evento no se perderá.")
    print("="*70 + "\n")
