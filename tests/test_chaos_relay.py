import pytest
import uuid
from sqlalchemy import text
from fintech_ledger.models import JournalEntry, Account, OutboxEvent
from fintech_ledger.idempotent_worker import process_transfer_event
from fintech_ledger.relay import run_relay_once

def test_chaos_worker_crash_mid_processing(db_session):
    """Demuestra que si el worker muere a la mitad, no se pierde dinero ni se cobra doble."""
    acc1 = Account(name="Cuenta A", account_type="ASSET")
    acc2 = Account(name="Cuenta B", account_type="ASSET")
    db_session.add(acc1)
    db_session.add(acc2)
    db_session.commit()

    tx_id = uuid.uuid4()
    
    # 1) El sistema recibe el webhook y guarda el evento en el Outbox
    event = OutboxEvent(
        aggregate_type="Transfer",
        aggregate_id=tx_id,
        event_type="TransferCreated",
        payload={
            "tx_id": str(tx_id),
            "from_account": str(acc1.id),
            "to_account": str(acc2.id),
            "amount": 1000.00
        }
    )
    db_session.add(event)
    db_session.commit()

    # 2) EL CAOS: El worker procesa la transferencia (mueve dinero + idempotencia)
    # pero el proceso muere (kill -9) ANTES de poder marcar el evento como "processed_at".
    process_transfer_event(db_session, tx_id, acc1.id, acc2.id, 1000.00)
    
    # Verificación 1: El evento sigue colgado en el Outbox (processed_at es None)
    db_session.expire_all()
    event_db = db_session.query(OutboxEvent).filter(OutboxEvent.aggregate_id == tx_id).first()
    assert event_db.processed_at is None, "El evento debería haber quedado sin procesar."

    # 3) EL REINICIO: El sistema arranca de nuevo. El Relay lee el Outbox.
    processed = run_relay_once(db_session)
    
    # Verificación 2: El Relay recogió el evento, vio que ya estaba en idempotencia y lo marcó como procesado.
    db_session.expire_all()
    event_db = db_session.query(OutboxEvent).filter(OutboxEvent.aggregate_id == tx_id).first()
    assert event_db.processed_at is not None, "El evento debería estar procesado tras el reinicio."
    
    # Verificación 3: SOLO hay 2 asientos contables en la BD. ¡No se cobró dos veces!
    journal_count = db_session.query(JournalEntry).filter(JournalEntry.transaction_id == tx_id).count()
    assert journal_count == 2, f"¡ALERTA! Se cobró dos veces. Asientos: {journal_count}"

    print("\n" + "="*70)
    print("CAOS SUPERADO: El worker procesó el dinero pero murió antes de actualizar el Outbox.")
    print("Al reiniciar, el Relay recuperó el evento, la idempotencia bloqueó el doble cobro,")
    print("y el sistema se curó a sí mismo.")
    print("El usuario solo fue cobrado UNA VEZ. (Exactly-Once Effect).")
    print("="*70 + "\n")
