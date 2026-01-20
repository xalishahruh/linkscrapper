from pydantic import BaseModel, HttpUrl
from uuid import uuid4


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    follow_redirects: bool = True
    max_redirects: int = 10

class AnalyzeResponse(BaseModel):
    analysis_id: str
    url:str
    status: str
    message: str