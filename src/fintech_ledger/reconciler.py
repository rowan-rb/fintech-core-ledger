from sqlalchemy import func
from fintech_ledger.models import JournalEntry, OutboxEvent

class ReconciliationError(Exception):
    """Se lanza cuando el libro mayor no cuadra."""
    pass

def reconcile_ledger(db_session):
    """
    Motor de auditoría contable.
    Verifica la invariante de Doble Entrada: SUM(amount) debe ser exactamente 0.
    También busca transacciones atascadas en el Outbox.
    """
    # 1) Verificar que la suma de todos los asientos es CERO
    total_balance = db_session.query(func.sum(JournalEntry.amount)).scalar()
    
    if total_balance is None:
        total_balance = 0.0
        
    if abs(total_balance) > 0.0001:  # Tolerancia para flotantes
        raise ReconciliationError(
            f"FALLO CRÍTICO: El libro mayor no cuadra. Descuadre de {total_balance}€. "
            "Se ha creado o destruido dinero."
        )

    # 2) Verificar que no hay eventos colgados para siempre
    pending_events = db_session.query(OutboxEvent).filter(
        OutboxEvent.processed_at == None
    ).count()

    return {
        "status": "ok",
        "total_balance": total_balance,
        "pending_outbox_events": pending_events
    }
