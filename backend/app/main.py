from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.app.api.analyze import router as analyze_router
from backend.app.db import Base, engine, SessionLocal
from backend.app.models.db_models import Analysis
from backend.app.models import db_models  # IMPORTANT: registers models
import asyncio
import json

app = FastAPI(
    title="Link Scrapper API",
    description="Backend API to analyze URLS and detect potential threats",
    version="1.0",

)
Base.metadata.create_all(bind=engine)

app.include_router(analyze_router)

@app.websocket("/ws/status/{analysis_id}")
async def websocket_endpoint(websocket: WebSocket, analysis_id: str):
    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            row = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not row:
                await websocket.send_json({"error": "Not found"})
                db.close()
                break
            
            data = {
                "status": row.status,
                "progress": row.progress,
                "message": row.progress_message
            }
            
            if row.result_json:
                data["result"] = json.loads(row.result_json)
                
            await websocket.send_json(data)
            
            if row.status in ["done", "error"]:
                db.close()
                break
                
            db.close()
            await asyncio.sleep(1) # poll db every second
    except WebSocketDisconnect:
        pass

@app.get("/")
def root():
    return {"status": "LinkScrapper API is running"}