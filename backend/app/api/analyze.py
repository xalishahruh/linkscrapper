from __future__ import annotations

import asyncio
import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.fetcher import fetch_url
from backend.app.core.scoring import assess_risk
from backend.app.core.signals import extract_signals
from backend.app.db import SessionLocal, get_db
from backend.app.models.db_models import Analysis
from backend.app.models.schemas import AnalyzeRequest, AnalyzeAccepted

router = APIRouter()


async def run_analysis_job(
    analysis_id: str,
    input_url: str,
    follow_redirects: bool,
    max_redirects: int,
) -> None:
    """
    Background job:
    - marks DB row as running
    - fetches URL and computes signals + risk
    - stores final result in DB
    """
    db = SessionLocal()
    try:
        row = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not row:
            return

        row.status = "running"
        row.updated_at = datetime.utcnow()
        db.commit()

        fetch_result = await fetch_url(
            url=input_url,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
        )

        signals = extract_signals(fetch_result)
        assessment = assess_risk(signals)

        payload = {
            "analysis_id": analysis_id,
            "url": input_url,
            "status": "done",
            "message": f"Risk {assessment.risk_level} ({assessment.risk_score}/100)",
            "final_url": fetch_result.final_url,
            "http_status": fetch_result.status_code,
            "redirect_chain": fetch_result.redirect_chain,
            "content_type": fetch_result.content_type,
            "server": fetch_result.server,
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level,
            "reasons": assessment.reasons,
        }

        row.status = "done"
        row.result_json = json.dumps(payload)
        row.error = None
        row.updated_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        row = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if row:
            row.status = "error"
            row.error = str(e)
            row.updated_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


@router.post("/analyze", response_model=AnalyzeAccepted)
async def analyze(
    analyze_request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new analysis job row, enqueue async processing, return analysis_id immediately.
    """
    analysis_id = str(uuid4())
    input_url = str(analyze_request.url)

    row = Analysis(
        id=analysis_id,
        input_url=input_url,
        status="queued",
        updated_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()

    asyncio.create_task(
        run_analysis_job(
            analysis_id=analysis_id,
            input_url=input_url,
            follow_redirects=analyze_request.follow_redirects,
            max_redirects=analyze_request.max_redirects,
        )
    )

    return {
        "analysis_id": analysis_id,
        "status": "queued",
        "message": "Job queued. Use GET /analysis/{analysis_id} to retrieve results.",
    }


@router.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """
    Retrieve analysis status or final result from the database.
    """
    row = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if row.status == "done" and row.result_json:
        return json.loads(row.result_json)

    return {
        "analysis_id": row.id,
        "url": row.input_url,
        "status": row.status,
        "error": row.error,
    }
