from fastapi import FastAPI
from backend.app.api.analyze import router as analyze_router
from backend.app.db import Base, engine
from backend.app.models import db_models  # IMPORTANT: registers models

app = FastAPI(
    title="Link Scrapper API",
    description="Backend API to analyze URLS and detect potential threats",
    version="1.0",

)
Base.metadata.create_all(bind=engine)

app.include_router(analyze_router)
@app.get("/")
def root():
    return {"status": "LinkScrapper API is running"}