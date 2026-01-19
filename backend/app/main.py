from fastapi import FastAPI

app = FastAPI(
    title="Link Scrapper API",
    description="Backend API to analyze URLS and detect potential threats",
    version="1.0",

)

@app.get("/")
def root():
    return {"status": "LinkScrapper API is running"}