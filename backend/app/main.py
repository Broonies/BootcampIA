# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel, Field
from typing import List, Dict, Any
import re

from app.llm import EpitechLLMService
from app.scrapper import scrape_url
from app.mcp_sim import MCPSimulator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des services
llm_service = EpitechLLMService()
mcp = MCPSimulator()


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)


def json_safe(value: Any):
    """
    Empêche tout type non JSON-sérialisable de faire planter FastAPI
    """
    if isinstance(value, set):
        return list(value)
    return value


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # 🔒 Validation défensive (Swagger / clients foireux)
        if not isinstance(request.history, list):
            raise HTTPException(
                status_code=400,
                detail="history must be a list of {role, content}"
            )

        # 1. Détection MCP
        tool_needed = mcp.detect_tool_needed(request.message)
        context: str = ""

        if tool_needed == "scrape_website":
            urls = re.findall(r'https?://[^\s]+', request.message)
            if urls:
                scraped = scrape_url(urls[0])
                if scraped.get("success"):
                    context = (
                        "Données scrapées:\n"
                        f"Titre: {scraped.get('title')}\n"
                        f"Contenu: {scraped.get('content', '')[:2000]}"
                    )

        # 2. Appel LLM
        response = llm_service.chat(
            message=request.message,
            context=context,
            history=request.history
        )
        

        # 3. Réponse JSON safe
        payload = {
    "response": response,
    "scraped_data": context if context else None
}
        return JSONResponse(
    status_code=200,
    content=jsonable_encoder(payload)
)

    except HTTPException:
        raise
    except Exception as e:
        # Log utile en dev
        print("❌ ERROR /api/chat:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "api": "api.ia.epitech.bzh",
        "model": "qwen3:30b"
    }
