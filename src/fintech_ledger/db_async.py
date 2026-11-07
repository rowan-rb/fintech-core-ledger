from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fintech_ledger.settings import settings

# Convertimos la URL de postgresql:// a postgresql+asyncpg://
async_url = settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    async_url, 
    pool_size=50, 
    max_overflow=100, 
    pool_pre_ping=True
)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)
