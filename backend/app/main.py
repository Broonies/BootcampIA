# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import traceback
import json

from .llm import EpitechLLMService
from .mcp_sim import MCPSimulator
from .models import ChatRequest
from .formatters import (
    format_fuel_results,
    format_traffic_results,
    format_parking_results,
    format_drive_time_results,
)

app = FastAPI(title="API Chatbot IA Local")

# --- MODIFICATION 1 : CORS permissifs pour le dev ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines (pratique pour le dev)
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des services
llm_service = EpitechLLMService()
mcp = MCPSimulator()


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        print(f"📨 Message reçu: {request.message}")
        print(f"📍 Lat/Lon reçues: {request.latitude}, {request.longitude}")
        if request.latitude and request.longitude:
            print(f"✓ Position GPS valide: ({request.latitude}, {request.longitude})")
        else:
            print(f"✗ Position GPS manquante ou None")

        # 1. MCP – détection + exécution
        mcp_result = mcp.process_message(
            request.message,
            user_location=(request.latitude, request.longitude) if request.latitude and request.longitude else None
        )
        tool_used = mcp_result.get("tool")

        context = ""
        raw_results = None

        # 🔒 Bloquer tout ce qui n’est pas mobilité
        if not tool_used:
            return {
                "response": (
                    "🚗 Je suis un assistant mobilité Rennes.\n\n"
                    "Je peux t'aider pour :\n"
                    "• prix des carburants\n"
                    "• stations essence\n"
                    "• parkings\n"
                    "• trafic et itinéraires\n\n"
                    "Pose-moi une question liée à tes déplacements."
                ),
                "tool_used": None,
                "data": None
            }

        # 2. Outils MCP (fuel, traffic, etc.)
        if tool_used != "scrape_website":
            print(f"🔧 Outil MCP détecté: {tool_used}")

            # Format texte pour le LLM
            if tool_used == "get_traffic_status":
                context = format_traffic_results(mcp_result)
            elif tool_used == "get_parking_status":
                context = format_parking_results(mcp_result)
            elif tool_used == "estimate_drive_time":
                context = format_drive_time_results(mcp_result)
            else:
                context = format_fuel_results(mcp_result)

            # Extraction données brutes pour le frontend
            data_content = mcp_result.get("result", {})

            if data_content.get("success"):
                if tool_used == "get_cheapest_station":
                    raw_results = data_content.get("cheapest_stations", [])
                elif tool_used == "search_fuel_prices":
                    raw_results = data_content.get("results", [])

            print(f"📊 Contexte généré: {context[:200]}...")

        # 3. Scraping de page web si URL (non implémenté - outil reservé pour futur usage)
        else:
            context = ""

        # 4. Prompt LLM verrouillé mobilité Rennes
        if context:
            system_prompt = f"""
Tu es un assistant IA spécialisé exclusivement dans l'aide aux automobilistes sur Rennes Métropole.

Tu n'as accès qu'aux données suivantes :
{context}

Tu n'as PAS le droit de :
- donner des conseils généraux
- répondre à des questions hors mobilité
- inventer des prix, itinéraires ou parkings
- utiliser des connaissances externes

Si l'utilisateur demande autre chose que :
- carburant
- parkings
- trafic
- itinéraires
tu dois répondre :
"Je suis un assistant mobilité Rennes."
"""
            full_message = f"{system_prompt}\n\nQuestion: {request.message}"
        else:
            full_message = request.message

        # 5. Appel LLM
        print("🤖 Appel au LLM...")
        response = llm_service.chat(
            message=full_message,
            context="",
            history=request.history
        )
        print("✅ Réponse générée")

        # 6. Réponse API
        return {
            "response": response,
            "tool_used": tool_used,
            "data": raw_results,
            "context": context
        }

    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "api": "api.ia.epitech.bzh",
        "model": "qwen3:30b",
        "mcp_tools": list(mcp.tools.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
