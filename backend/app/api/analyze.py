from fastapi import APIRouter, HTTPException
from uuid import uuid4

from backend.app.models.schemas import AnalyzeRequest, AnalyzeResponse
from backend.app.core.fetcher import fetch_url

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(analyze_request: AnalyzeRequest):
    analysis_id =str(uuid4())

    return AnalyzeResponse(
        analysis_id=analysis_id,
        url = str(analyze_request.url),
        status ="accepted",
        message = "URL accepted for analysis"
    )