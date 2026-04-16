from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from agents.web_agent import WebChatbotAgent
from core.database.manager import DatabaseManager
from core.ingestion import KnowledgeIngestor
import uvicorn
import asyncio
from workflow import scrape_task, capture_lead_task # Import workflow tasks

app = FastAPI(title="Fastigo AI Chatbot API")

# Initialize shared components
db = DatabaseManager()
agent = WebChatbotAgent(db)
ingestor = KnowledgeIngestor(db)

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ScrapeRequest(BaseModel):
    url: str = "https://fastigo.co/"
    max_pages: Optional[int] = 10

@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "agent": agent.name,
        "database": "connected" if db.mongo_client else "mongo_disconnected"
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        response = agent.process_transcript(request.message, session_id=request.session_id)
        return {"response": response, "session_id": request.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape")
async def trigger_scrape(request: ScrapeRequest):
    # Trigger distributed workflow task
    scrape_task.trigger(url=request.url, max_pages=request.max_pages)
    return {"message": f"Scraping workflow started for {request.url}. Track it on your Render dashboard."}

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
