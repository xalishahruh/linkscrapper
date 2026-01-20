from fastapi import APIRouter, HTTPException
from uuid import uuid4

from backend.app.models.schemas import AnalyzeRequest, AnalyzeResponse

from backend.app.core.fetcher import fetch_url
from backend.app.core.signals import extract_signals
from backend.app.core.scoring import assess_risk
router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(analyze_request: AnalyzeRequest):
    analysis_id =str(uuid4())
    input_url = str(analyze_request.url)

    try:
        fetch_result = await fetch_url(
            url=input_url,
            follow_redirects=analyze_request.follow_redirects,
            max_redirects=analyze_request.max_redirects,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    signals = extract_signals(fetch_result)
    assessment = assess_risk(signals)

    return AnalyzeResponse(
        analysis_id=analysis_id,
        url=input_url,
        status="scored",
        message=f"Risk {assessment.risk_level} ({assessment.risk_score}/100)",
        final_url=fetch_result.final_url,
        http_status=fetch_result.status_code,
        redirect_chain=fetch_result.redirect_chain,
        content_type=fetch_result.content_type,
        server=fetch_result.server,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        reasons=assessment.reasons,

    )