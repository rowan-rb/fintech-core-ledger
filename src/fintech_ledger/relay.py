import time
from datetime import datetime, timezone
from sqlalchemy import text
from fintech_ledger.models import OutboxEvent
from fintech_ledger.idempotent_worker import process_transfer_event, DuplicateTransactionError
import uuid

def run_relay_once(db_session):
    """
    Simula el worker que lee del Outbox y procesa los eventos.
    Si el proceso muere a la mitad, el evento no se marca como procesado.
    """
    # 1) Buscar eventos no procesados
    events = db_session.query(OutboxEvent).filter(
        OutboxEvent.processed_at == None
    ).with_for_update(skip_locked=True).all()

    processed_count = 0
    for event in events:
        payload = event.payload
        
        # 2) Procesar el evento (aquí es donde puede fallar y morir)
        try:
            process_transfer_event(
                db_session, 
                uuid.UUID(payload['tx_id']), 
                uuid.UUID(payload['from_account']), 
                uuid.UUID(payload['to_account']), 
                payload['amount']
            )
        except DuplicateTransactionError:
            # Si ya se procesó antes del crash, lo ignoramos.
            pass
        
        # 3) Marcar como procesado (Si el proceso muere ANTES de esta línea, el evento se re-procesará)
        event.processed_at = datetime.now(timezone.utc)
        db_session.commit()
        processed_count += 1
        
    return processed_count
