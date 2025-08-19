"""
Database models and helper for persisting analyses.
"""

from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
)
from sqlalchemy.orm import sessionmaker, declarative_base
import json

DB_PATH = Path(__file__).resolve().parents[2] / "analysis.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


class CompanyAnalysis(Base):
    __tablename__ = "company_analysis"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), index=True)
    company_name = Column(String(256))
    sector = Column(String(128))
    market_cap = Column(Float)
    overall_score = Column(Float)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    details_json = Column(Text)  # full criteria dict


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def save_company_analysis(evaluation: Dict[str, Any]) -> None:
    session = SessionLocal()
    try:
        record = CompanyAnalysis(
            symbol=evaluation.get("symbol"),
            company_name=evaluation.get("company_name"),
            sector=evaluation.get("sector"),
            market_cap=float(evaluation.get("market_cap", 0) or 0),
            overall_score=float(evaluation.get("overall_score", 0) or 0),
            analysis_date=datetime.fromisoformat(evaluation.get("analysis_date"))
            if evaluation.get("analysis_date")
            else datetime.utcnow(),
            details_json=json.dumps(evaluation),
        )
        session.add(record)
        session.commit()
    finally:
        session.close()




