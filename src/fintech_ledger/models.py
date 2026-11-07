from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=text('NOW()'))

class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=False)
    amount = Column(Numeric(19, 4), nullable=False)
    created_at = Column(DateTime, server_default=text('NOW()'))

class OutboxEvent(Base):
    __tablename__ = 'outbox'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime, server_default=text('NOW()'))
    processed_at = Column(DateTime, nullable=True)

class IdempotencyKey(Base):
    __tablename__ = 'idempotency_keys'
    key = Column(String(255), primary_key=True)
    created_at = Column(DateTime, server_default=text('NOW()'))
