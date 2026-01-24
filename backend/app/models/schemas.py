from pydantic import BaseModel, HttpUrl, Field
from uuid import uuid4
from typing import Optional, List


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    follow_redirects: bool = True
    max_redirects: int = Field(default=10, ge=0, le=20)

class AnalyzeResponse(BaseModel):
    analysis_id: str
    url:str
    status: str
    message: str

    final_url: Optional[str] = None
    http_status: Optional[int] = None
    redirect_chain: Optional[List[str]] = None
    content_type: Optional[str] = None
    server: Optional[str] = None

    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    reasons: Optional[List[str]] = None

class AnalyzeAccepted(BaseModel):
    analysis_id: str
    status: str
    message: str