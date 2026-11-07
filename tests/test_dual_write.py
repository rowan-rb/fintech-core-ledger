import pytest
import unittest.mock
import uuid
from fintech_ledger.naive_transfer import execute_transfer
from fintech_ledger.models import JournalEntry, Account

def test_dual_write_crash_loses_money(db_session):
    """Demostrar que el antipatrón Dual-Write causa pérdida de dinero."""
    # Crear cuentas de prueba (para cumplir con la Foreign Key)
    acc1 = Account(name="Cuenta A", account_type="ASSET")
    acc2 = Account(name="Cuenta B", account_type="ASSET")
    db_session.add(acc1)
    db_session.add(acc2)
    db_session.commit()

    amount = 5000.00
    tx_id = uuid.uuid4()
    
    # Simulamos el canal de RabbitMQ y forzamos el fallo en basic_publish
    mock_channel = unittest.mock.MagicMock()

    with unittest.mock.patch.object(
        mock_channel,
        "basic_publish",
        side_effect=RuntimeError("Simulated crash: network lost"),
    ):
        with pytest.raises(RuntimeError, match="network lost"):
            execute_transfer(
                db_session,
                mock_channel,
                acc1.id,
                acc2.id,
                amount,
                tx_id,
            )

    # VERIFICACIÓN DEL BUG: el dinero SÍ se movió en la BD
    count = db_session.query(JournalEntry).filter(
        JournalEntry.transaction_id == tx_id
    ).count()
    assert count == 2, f"Se esperaban 2 asientos, se encontraron {count}"

    # Verificar que NO hay nada en la cola (el publish falló)
    assert mock_channel.basic_publish.call_count == 0

    print("\n" + "="*70)
    print("BUG CONFIRMADO: Dinero movido en BD (2 asientos) pero evento perdido.")
    print("El dinero ha desaparecido.")
    print("="*70 + "\n")
