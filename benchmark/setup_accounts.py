from sqlalchemy import text
from fintech_ledger.db import SessionLocal
from fintech_ledger.models import Account

def setup_accounts(num=1000):
    print(f"Creando {num} cuentas...")
    db = SessionLocal()
    
    # TRUNCATE es una operación DDL, vacía las tablas instantáneamente 
    # y evita el error de ForeignKey sin disparar el trigger de DELETE.
    db.execute(text("TRUNCATE TABLE journal_entries, accounts, idempotency_keys, outbox CASCADE;"))
    db.commit()

    accounts = [Account(name=f"User_{i}", account_type="ASSET") for i in range(num)]
    db.add_all(accounts)
    db.commit()
    
    ids = [str(acc.id) for acc in accounts]
    db.close()
    return ids
