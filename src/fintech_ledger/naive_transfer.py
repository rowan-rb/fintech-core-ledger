import time
import json
import uuid
from datetime import datetime, timezone
import pika
from fintech_ledger.models import JournalEntry

def execute_transfer(db_session, rabbit_channel, from_acc, to_acc, amount, tx_id):
    # 1) Insertamos ambas líneas del asiento (Débito y Crédito)
    debit = JournalEntry(
        transaction_id=tx_id,
        account_id=from_acc,
        amount=amount,
    )
    credit = JournalEntry(
        transaction_id=tx_id,
        account_id=to_acc,
        amount=-amount, # Crédito es negativo
    )
    db_session.add(debit)
    db_session.add(credit)

    # 2) Commit a PostgreSQL
    db_session.commit()

    # 3) Publicamos al motor de mensajería (SIN transacción)
    time.sleep(0.1)  # Simula latencia de red real
    event = {
        "tx_id": str(tx_id),
        "type": "transfer",
        "from_account": str(from_acc),
        "to_account": str(to_acc),
        "amount": float(amount),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    rabbit_channel.basic_publish(
        exchange="",
        routing_key="transfers",
        body=json.dumps(event).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2),
    )
