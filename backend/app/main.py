# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import traceback
import json

from app.llm import EpitechLLMService
from backend.app.tools.scraper import scrape_url
from app.mcp_sim import MCPSimulator

app = FastAPI(title="Chatbot IA Local API")

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
    history: list = Field(default_factory=list)

class FuelSearchRequest(BaseModel):
    ville: str = None
    code_postal: str = None
    fuel_type: str = "Gazole"
    limit: int = 5

def format_fuel_results(mcp_result: dict) -> str:
    """Formate les résultats des prix de carburant pour le LLM"""
    if not mcp_result.get('success'):
        return f"❌ Erreur: {mcp_result.get('error', 'Erreur inconnue')}"
    
    tool = mcp_result.get('tool', 'search_fuel_prices')
    result = mcp_result.get('result', {})
    
    if tool == "get_cheapest_station":
        stations = result.get('cheapest_stations', [])
        location = result.get('location', 'inconnue')
        fuel_type = result.get('fuel_type', 'Gazole')
        
        if not stations:
            return f"Aucune station trouvée pour {location}"
        
        formatted = f"🚗 Top {len(stations)} stations les moins chères pour {fuel_type} à {location}:\n\n"
        
        for i, station in enumerate(stations, 1):
            formatted += f"{i}. {station['adresse']}, {station['ville']} ({station['cp']})\n"
            formatted += f"   💰 Prix: {station['price']:.3f} €/L\n"
            formatted += f"   🕒 Mis à jour: {station['updated']}\n\n"
        
        return formatted
    
    elif tool == "search_fuel_prices":
        stations = result.get('results', [])
        location = result.get('location', 'inconnue')
        fuel_type = result.get('fuel_type', 'Gazole')
        count = result.get('count', 0)
        
        if not stations:
            return f"Aucune station trouvée pour {location}"
        
        formatted = f"🔍 {count} stations trouvées pour {fuel_type} à {location}:\n\n"
        
        for i, station in enumerate(stations[:5], 1):  # Top 5
            formatted += f"{i}. {station['adresse']}, {station['ville']}\n"
            formatted += f"   💰 {station['price']:.3f} €/L\n\n"
        
        if count > 5:
            formatted += f"... et {count - 5} autres stations\n"
        
        return formatted
    
    elif tool == "get_fuel_stats":
        stats = result.get('stats', {})
        if 'error' in stats:
            return f"❌ {stats['error']}"
        
        gazole = stats.get('gazole', {})
        return f"""📊 Statistiques nationales ({stats.get('date', 'aujourd\'hui')}):

Total de stations: {stats.get('total_stations', 0)}

Prix du Gazole:
• Minimum: {gazole.get('min', 0):.3f} €/L
• Maximum: {gazole.get('max', 0):.3f} €/L
• Moyenne: {gazole.get('avg', 0):.3f} €/L
"""
    
    return "Résultat traité"

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        print(f"📨 Message reçu: {request.message}")
        
        # 1. Traiter avec MCP pour détecter l'intention
        mcp_result = mcp.process_message(request.message)
        tool_used = mcp_result.get('tool')
        
        context = ""
        
        # 2. Exécuter l'outil MCP si nécessaire
        if tool_used and tool_used != "scrape_website":
            print(f"🔧 Outil MCP détecté: {tool_used}")
            context = format_fuel_results(mcp_result)
            print(f"📊 Contexte généré: {context[:200]}...")
        
        # 3. Scraping classique si URL détectée
        elif tool_used == "scrape_website":
            import re
            urls = re.findall(r'https?://[^\s]+', request.message)
            if urls:
                scraped = scrape_url(urls[0])
                if scraped['success']:
                    context = f"""Données scrapées de {urls[0]}:
Titre: {scraped['title']}
Contenu: {scraped['content'][:1500]}"""
        
        # 4. Construire le prompt pour le LLM
        if context:
            system_prompt = f"""Tu es un assistant spécialisé dans l'aide aux automobilistes pour trouver les meilleurs prix de carburant.

Données disponibles:
{context}

Instructions:
- Réponds de manière claire et concise
- Mets en avant les informations les plus pertinentes
- Utilise des émojis pour rendre la réponse plus lisible
- Si c'est une question sur les prix, base-toi UNIQUEMENT sur les données fournies"""
            
            full_message = f"{system_prompt}\n\nQuestion de l'utilisateur: {request.message}"
        else:
            full_message = request.message
        
        # 5. Appeler le LLM
        print("🤖 Appel au LLM...")
        response = llm_service.chat(
            message=full_message,
            context="",
            history=request.history
        )
        
        print(f"✅ Réponse générée")
        
        return {
            "response": response,
            "tool_used": tool_used,
            "scraped_data": context if context else None
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

@app.post("/api/fuel/search")
async def search_fuel(request: FuelSearchRequest):
    """Endpoint dédié pour la recherche de prix de carburant"""
    try:
        params = {
            "ville": request.ville,
            "code_postal": request.code_postal,
            "fuel_type": request.fuel_type,
            "limit": request.limit
        }
        
        result = mcp.execute_tool("get_cheapest_station", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fuel/stats")
async def fuel_stats():
    """Endpoint pour les statistiques carburant"""
    try:
        result = mcp.execute_tool("get_fuel_stats", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fuel/refresh")
async def refresh_fuel_data():
    """Force le rafraîchissement des données carburant"""
    try:
        mcp.fuel_scraper.fetch_daily_prices(force_refresh=True)
        return {"status": "success", "message": "Données rafraîchies"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))