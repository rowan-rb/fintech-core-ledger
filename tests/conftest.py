import pytest
import pika
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fintech_ledger.settings import settings
from fintech_ledger.models import Base

@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión limpia para cada test, borrando los datos al terminar."""
    engine = create_engine(settings.DATABASE_URL)
    
    # Crear todas las tablas si no existen (por si acaso)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Limpieza profunda: borrar todo el contenido de las tablas después de cada test
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE journal_entries, accounts, idempotency_keys, outbox CASCADE;"))

@pytest.fixture(scope="function")
def rabbitmq_connection():
    params = pika.URLParameters(settings.RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    yield connection
    connection.close()

@pytest.fixture
def clean_queues(rabbitmq_connection):
    channel = rabbitmq_connection.channel()
    channel.queue_declare(queue='test', durable=False)
    channel.queue_purge(queue='test')
    channel.close()
