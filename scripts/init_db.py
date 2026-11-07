import os
import glob
from sqlalchemy import create_engine, text
from fintech_ledger.settings import settings

def init_db():
    print("Inicializando base de datos...")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    migrations_dir = os.path.join(base_dir, "migrations")
    
    # Buscar todos los archivos .sql y ordenarlos
    sql_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
    
    if not sql_files:
        print("ERROR: No se encontraron archivos SQL.")
        return
        
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.begin() as conn:
        # Limpieza inicial
        conn.execute(text("DROP TABLE IF EXISTS journal_entries CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS accounts CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS idempotency_keys CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS outbox CASCADE;"))
        
        # Ejecutar cada archivo SQL en orden
        for file_path in sql_files:
            filename = os.path.basename(file_path)
            print(f"Ejecutando {filename}...")
            with open(file_path, "r") as f:
                sql = f.read()
            conn.execute(text(sql))
            
    print("Esquema y triggers creados correctamente.")

if __name__ == "__main__":
    init_db()
