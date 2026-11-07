from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# 1. Configurar OpenTelemetry ANTES de importar FastAPI
resource = Resource.create({"service.name": "fintech-ledger"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://127.0.0.1:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# 2. Importar FastAPI y el resto
from fastapi import FastAPI, Response, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from fintech_ledger.db_async import async_engine, AsyncSessionLocal
from fintech_ledger.outbox_transfer_async import execute_transfer_outbox_async
import pika
from fintech_ledger.settings import settings
import uuid

app = FastAPI()

# 3. Instrumentar FastAPI y SQLAlchemy
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=async_engine.sync_engine)

class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float

@app.get("/health")
async def health(response: Response):
    db_status = "ok"
    mq_status = "ok"
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
    try:
        params = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        connection.close()
    except Exception as e:
        mq_status = f"error: {str(e)}"
    if db_status != "ok" or mq_status != "ok":
        response.status_code = 500
        return {"status": "error", "db": db_status, "mq": mq_status}
    return {"status": "ok", "db": db_status, "mq": mq_status}

@app.post("/transfer")
async def create_transfer(req: TransferRequest):
    async with AsyncSessionLocal() as session:
        try:
            tx_id = uuid.uuid4()
            await execute_transfer_outbox_async(session, uuid.UUID(req.from_account), uuid.UUID(req.to_account), req.amount, tx_id)
            return {"status": "accepted", "tx_id": str(tx_id)}
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


