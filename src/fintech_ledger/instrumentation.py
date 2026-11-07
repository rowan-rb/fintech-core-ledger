from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from fintech_ledger.tracing import tracer
from fintech_ledger.api import app
from fintech_ledger.db import engine

# Instrumentar FastAPI y SQLAlchemy
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

# El app original se importa desde fintech_ledger.api
