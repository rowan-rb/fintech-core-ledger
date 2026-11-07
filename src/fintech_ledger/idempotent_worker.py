from sqlalchemy.exc import IntegrityError
from fintech_ledger.models import JournalEntry, IdempotencyKey

class DuplicateTransactionError(Exception):
    """Se lanza cuando un mensaje ya ha sido procesado."""
    pass

def process_transfer_event(db_session, tx_id, from_acc, to_acc, amount):
    """
    Procesa un evento de transferencia de forma idempotente.
    Si la transacción ya existe en idempotency_keys, lanza una excepción
    y no vuelve a mover el dinero.
    """
    try:
        # 1) Intentar registrar la clave de idempotencia
        # Si ya existe, el PRIMARY KEY saltará y lanzará IntegrityError
        idempotency_record = IdempotencyKey(key=str(tx_id))
        db_session.add(idempotency_record)
        db_session.flush()  # Fuerza el INSERT para que salte el error si hay duplicado

        # 2) Si no hubo error, movemos el dinero (Débito y Crédito)
        debit = JournalEntry(transaction_id=tx_id, account_id=from_acc, amount=amount)
        credit = JournalEntry(transaction_id=tx_id, account_id=to_acc, amount=-amount)
        db_session.add(debit)
        db_session.add(credit)

        # 3) Commit final de todo el bloque
        db_session.commit()
        return True

    except IntegrityError:
        # El mensaje ya fue procesado antes. Hacemos rollback y lo ignoramos.
        db_session.rollback()
        raise DuplicateTransactionError(f"Transacción {tx_id} ya procesada. Ignorando duplicado.")
