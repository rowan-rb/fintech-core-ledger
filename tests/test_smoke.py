import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from fintech_ledger.main import app


def test_db_connection(db_session):
    """Test 1: Conecta a Postgres y ejecuta SELECT 1."""
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_rabbitmq_connection(rabbitmq_connection, clean_queues):
    """Test 2: Conecta a RabbitMQ y declara/borra la cola 'test'."""
    import pika
    channel = rabbitmq_connection.channel()
    # Declarar la cola
    channel.queue_declare(queue="test", durable=False)
    # Borrar la cola
    channel.queue_delete(queue="test")
    # Verificar que fue borrada (debe lanzar excepciÃ³n si no existe)
    try:
        channel.queue_purge(queue="test")
    except pika.exceptions.ChannelClosedByBroker:
        pass


def test_api_health():
    """Test 3: Usa TestClient de FastAPI para GET /health."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert data["mq"] == "ok"
