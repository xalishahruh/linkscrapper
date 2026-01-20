from fastapi import FastAPI
from backend.app.api.analyze import router as analyze_router
app = FastAPI(
    title="Link Scrapper API",
    description="Backend API to analyze URLS and detect potential threats",
    version="1.0",

)
app.include_router(analyze_router)
@app.get("/")
def root():
    return {"status": "LinkScrapper API is running"}