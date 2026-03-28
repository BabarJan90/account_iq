from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./accountiq.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String)
    vendor = Column(String)
    amount = Column(Float)
    category = Column(String, nullable=True)
    description = Column(String, nullable=True)
    risk_score = Column(Float, nullable=True)       # from fuzzy logic
    risk_label = Column(String, nullable=True)      # low / medium / high
    is_anomaly = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)       # XAI explanation
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """GDPR-compliant audit trail for every AI decision made."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String)          # e.g. 'risk_scored', 'report_generated'
    transaction_id = Column(Integer, nullable=True)
    input_data = Column(Text)        # what data was used
    output_data = Column(Text)       # what decision was made
    model_used = Column(String)      # which AI model was involved
    justification = Column(Text)     # human-readable reason (XAI)


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(String)        # 'client_letter', 'anomaly_report', 'summary'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    transaction_ids = Column(Text)   # comma-separated IDs used


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
