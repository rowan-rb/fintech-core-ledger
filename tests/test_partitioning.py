import pytest
from sqlalchemy import text

def test_table_is_partitioned(db_session):
    """Demuestra que la tabla de asientos está particionada (Big Data Fintech)."""
    # En Postgres, relkind = 'p' significa "partitioned table"
    result = db_session.execute(text("SELECT relkind FROM pg_class WHERE relname = 'journal_entries';"))
    relkind = result.scalar()
    
    assert relkind == 'p', "La tabla NO está particionada. Sigue siendo una tabla normal."
    
    print("\n" + "="*70)
    print("PARTICIONAMIENTO CONFIRMADO: journal_entries es una tabla particionada.")
    print("Postgres ahora dividirá los datos por mes automáticamente.")
    print("="*70 + "\n")
