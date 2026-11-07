from fintech_ledger.models import JournalEntry, OutboxEvent

async def execute_transfer_outbox_async(async_session, from_acc, to_acc, amount, tx_id):
    """
    Version asincrona del Transactional Outbox.
    No bloquea el event loop de Python.
    """
    debit = JournalEntry(transaction_id=tx_id, account_id=from_acc, amount=amount)
    credit = JournalEntry(transaction_id=tx_id, account_id=to_acc, amount=-amount)
    async_session.add(debit)
    async_session.add(credit)

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
    async_session.add(outbox_event)

    await async_session.commit()
    return outbox_event.id
