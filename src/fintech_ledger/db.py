from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fintech_ledger.settings import settings

# Aumentamos el pool a 50 conexiones concurrentes (por defecto son 5)
# pool_pre_ping=True evita errores si la DB reinicia la conexión
engine = create_engine(
    settings.DATABASE_URL, 
    pool_size=50, 
    max_overflow=100, 
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
