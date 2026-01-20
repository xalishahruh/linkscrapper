from fastapi import APIRouter, HTTPException
from uuid import uuid4

from backend.app.models.schemas import AnalyzeRequest, AnalyzeResponse
from backend.app.core.fetcher import fetch_url

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(analyze_request: AnalyzeRequest):
    analysis_id =str(uuid4())
    input_url = str(analyze_request.url)

    try:
        result = await fetch_url(
        url=input_url,
        follow_redirects=analyze_request.follow_redirects,
        max_redirects=analyze_request.max_redirects,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AnalyzeResponse(
        analysis_id=analysis_id,
        url = str(analyze_request.url),
        status ="accepted",
        message = f"Fetched with status {result.status_code} (hops: {len(result.redirect_chain)})",
        final_url = result.final_url,
        http_status=result.status_code,
        redirect_chain = result.redirect_chain,
        content_type=result.content_type,
        server=result.server,

    )