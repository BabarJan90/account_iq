"""Transactions router — CRUD + bulk analysis."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from db.database import get_db, Transaction, AuditLog
from services.fuzzy_risk import fuzzy_scorer
from services.nlp_service import nlp_service
from datetime import datetime
import json

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionCreate(BaseModel):
    date: str
    vendor: str
    amount: float
    description: Optional[str] = ""


class TransactionResponse(BaseModel):
    id: int
    date: str
    vendor: str
    amount: float
    category: Optional[str]
    description: Optional[str]
    risk_score: Optional[float]
    risk_label: Optional[str]
    is_anomaly: bool
    explanation: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    risk_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)
    if risk_filter:
        query = query.filter(Transaction.risk_label == risk_filter)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=TransactionResponse)
def create_transaction(tx: TransactionCreate, db: Session = Depends(get_db)):
    category = nlp_service.classify_transaction(tx.vendor, tx.description or "", tx.amount)
    risk_score, risk_label, explanation = fuzzy_scorer.score(tx.amount, tx.vendor)
    is_anomaly = risk_score > 70

    db_tx = Transaction(
        date=tx.date,
        vendor=tx.vendor,
        amount=tx.amount,
        category=category,
        description=tx.description,
        risk_score=risk_score,
        risk_label=risk_label,
        is_anomaly=is_anomaly,
        explanation=explanation,
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)

    # GDPR audit log
    log = AuditLog(
        action="risk_scored",
        transaction_id=db_tx.id,
        input_data=json.dumps({"vendor": tx.vendor, "amount": tx.amount}),
        output_data=json.dumps({"risk_score": risk_score, "risk_label": risk_label}),
        model_used="FuzzyLogicV1",
        justification=explanation,
    )
    db.add(log)
    db.commit()

    return db_tx


@router.post("/analyse-all")
def analyse_all_transactions(db: Session = Depends(get_db)):
    """Score all unanalysed transactions using fuzzy logic + XAI."""
    transactions = db.query(Transaction).filter(Transaction.risk_score == None).all()
    updated = 0
    for tx in transactions:
        risk_score, risk_label, explanation = fuzzy_scorer.score(tx.amount, tx.vendor)
        tx.risk_score = risk_score
        tx.risk_label = risk_label
        tx.is_anomaly = risk_score > 70
        tx.explanation = explanation
        tx.category = nlp_service.classify_transaction(
            tx.vendor, tx.description or "", tx.amount
        )
        updated += 1

    db.commit()
    return {"message": f"Analysed {updated} transactions.", "updated": updated}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard statistics."""
    all_tx = db.query(Transaction).all()
    total_value = sum(t.amount for t in all_tx)
    risk_counts = {"low": 0, "medium": 0, "high": 0, "unscored": 0}
    for t in all_tx:
        label = t.risk_label or "unscored"
        risk_counts[label] = risk_counts.get(label, 0) + 1

    return {
        "total_transactions": len(all_tx),
        "total_value": round(total_value, 2),
        "risk_distribution": risk_counts,
        "anomaly_count": sum(1 for t in all_tx if t.is_anomaly),
    }
