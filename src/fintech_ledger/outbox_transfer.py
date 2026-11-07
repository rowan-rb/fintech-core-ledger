import json
import uuid
from fintech_ledger.models import JournalEntry, OutboxEvent

def execute_transfer_outbox(db_session, from_acc, to_acc, amount, tx_id):
    """
    Patrón Transactional Outbox:
    Guarda los asientos contables Y el evento en la misma transacción atómica.
    Si el commit falla, no se guarda nada. Si el commit pasa, el evento está a salvo.
    """
    # 1) Insertar asientos contables
    debit = JournalEntry(transaction_id=tx_id, account_id=from_acc, amount=amount)
    credit = JournalEntry(transaction_id=tx_id, account_id=to_acc, amount=-amount)
    db_session.add(debit)
    db_session.add(credit)

    # 2) Crear el evento en la tabla outbox (MISMA TRANSACCIÓN)
    event_payload = {
        "tx_id": str(tx_id),
        "type": "transfer",
        "from_account": str(from_acc),
        "to_account": str(to_acc),
        "amount": float(amount),
    }
    outbox_event = OutboxEvent(
        aggregate_type="Transfer",
        aggregate_id=tx_id,
        event_type="TransferCreated",
        payload=event_payload
    )
    db_session.add(outbox_event)

    # 3) COMMIT ATÓMICO (Todo o nada)
    db_session.commit()
    return outbox_event.id
