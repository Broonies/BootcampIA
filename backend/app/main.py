# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from llm import EpitechLLMService
from scraper import scrape_url
from mcp_sim import MCPSimulator

app = FastAPI()
llm_service = EpitechLLMService()
mcp = MCPSimulator()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: List[Dict] = []

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # 1. Détecter si un tool MCP est nécessaire
        tool_needed = mcp.detect_tool_needed(request.message)
        context = ""
        
        if tool_needed == "scrape_website":
            import re
            urls = re.findall(r'https?://[^\s]+', request.message)
            if urls:
                scraped = scrape_url(urls[0])
                if scraped['success']:
                    context = f"""Données scrapées:
Titre: {scraped['title']}
Contenu: {scraped['content'][:2000]}"""
        
        # 2. Appeler l'API Epitech
        response = llm_service.chat(
            message=request.message,
            context=context,
            history=request.history
        )
        
        return {
            "response": response,
            "scraped_data": context if context else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "api": "api.ia.epitech.bzh",
        "model": "qwen3:30b"
    }