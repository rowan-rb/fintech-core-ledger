import pytest
import uuid
from fintech_ledger.reconciler import reconcile_ledger, ReconciliationError
from fintech_ledger.models import Account, JournalEntry
from fintech_ledger.outbox_transfer import execute_transfer_outbox

def test_reconciliation_catches_imbalance(db_session):
    """Demuestra que el auditor detecta si alguien ha manipulado el dinero."""
    acc1 = Account(name="Cuenta A", account_type="ASSET")
    acc2 = Account(name="Cuenta B", account_type="ASSET")
    db_session.add(acc1)
    db_session.add(acc2)
    db_session.commit()

    # 1) Hacemos una transferencia normal (Débito -100, Crédito +100) -> Cuadra
    execute_transfer_outbox(db_session, acc1.id, acc2.id, 100.00, uuid.uuid4())
    
    # El auditor debe decir que todo está OK
    result = reconcile_ledger(db_session)
    assert result["status"] == "ok"
    assert result["total_balance"] == 0.0

    # 2) INYECTAMOS UN FALLO (Simulamos un bug en producción o un hackeo)
    # Alguien inyecta un asiento de +50.000€ por la cara sin el correspondiente débito.
    fake_hack = JournalEntry(
        transaction_id=uuid.uuid4(),
        account_id=acc1.id,
        amount=50000.00  # ¡Dinero creado de la nada!
    )
    db_session.add(fake_hack)
    db_session.commit()

    # 3) El auditor corre de nuevo y debe saltar la alarma
    with pytest.raises(ReconciliationError, match="Descuadre de 50000"):
        reconcile_ledger(db_session)

    print("\n" + "="*70)
    print("RECONCILIACIÓN CONFIRMADA: El auditor detectó 50.000€ creados de la nada.")
    print("La invariante contable (Débitos + Créditos = 0) se ha violado.")
    print("="*70 + "\n")
