# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import traceback
import json

from app.llm import EpitechLLMService
from app.tools.scraper import scrape_url
from app.mcp_sim import MCPSimulator

app = FastAPI(title="Chatbot IA Local API")

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

class ChatRequest(BaseModel):
    message: str
    history: list = Field(default_factory=list)

class FuelSearchRequest(BaseModel):
    ville: str = None
    code_postal: str = None
    fuel_type: str = "Gazole"
    limit: int = 5

def format_fuel_results(mcp_result: dict) -> str:
    """Formate les résultats MCP carburant pour le LLM"""

    tool = mcp_result.get("tool")
    data = mcp_result.get("result", {})

    if not data.get("success"):
        return f"❌ Erreur: {data.get('error', 'Erreur inconnue')}"

    if tool == "get_cheapest_station":
        stations = data.get("cheapest_stations", [])
        location = data.get("location", "inconnue")
        fuel_type = data.get("fuel_type", "Gazole")

        if not stations:
            return f"Aucune station trouvée pour {location}"

        out = f"🚗 Stations les moins chères pour {fuel_type} à {location}:\n\n"
        for i, s in enumerate(stations, 1):
            out += (
                f"{i}. {s['adresse']}, {s['ville']} ({s['cp']})\n"
                f"   💰 {s['price']:.3f} €/L\n"
                f"   🕒 {s['updated']}\n\n"
            )
        return out

    if tool == "search_fuel_prices":
        stations = data.get("results", [])
        location = data.get("location", "inconnue")
        fuel_type = data.get("fuel_type", "Gazole")
        count = data.get("count", 0)

        if not stations:
            return f"Aucune station trouvée pour {location}"

        out = f"⛽ {count} stations pour {fuel_type} à {location}:\n\n"
        for i, s in enumerate(stations[:5], 1):
            out += (
                f"{i}. {s['adresse']}, {s['ville']} ({s['cp']})\n"
                f"   💰 {s['price']:.3f} €/L\n\n"
            )
        return out

    if tool == "get_fuel_stats":
        stats = data.get("stats", {})
        gazole = stats.get("gazole", {})

        return (
            f"📊 Statistiques nationales ({stats.get('date')}):\n\n"
            f"Stations: {stats.get('total_stations')}\n"
            f"Gazole:\n"
            f"• Min: {gazole.get('min'):.3f} €/L\n"
            f"• Max: {gazole.get('max'):.3f} €/L\n"
            f"• Moyenne: {gazole.get('avg'):.3f} €/L\n"
        )

    return "Données MCP reçues mais non formatées"


def format_traffic_results(mcp_result: dict) -> str:
    """Formate les données de trafic Rennes pour le LLM"""

    data = mcp_result.get("result", {})

    if not data.get("success"):
        return f"❌ Erreur trafic: {data.get('error', 'Erreur inconnue')}"

    roads = data.get("roads", [])
    summary = data.get("summary", "Données de trafic")
    updated = data.get("updated", "maintenant")

    if not roads:
        return f"🟢 {summary} à Rennes (mis à jour à {updated})"

    txt = f"🚦 État du trafic Rennes - {summary} ({updated}):\n\n"

    # Regrouper par priorité pour meilleure lisibilité
    critical = [r for r in roads if r.get("priority") == "critique"]
    high = [r for r in roads if r.get("priority") == "haute"]
    medium = [r for r in roads if r.get("priority") == "moyen"]
    
    def _fmt(street: str, lat: float | None, lon: float | None) -> str:
        if lat is not None and lon is not None:
            return f"{street} ({lat:.5f}, {lon:.5f})"
        return street

    if critical:
        txt += "🚨 CRITIQUE:\n"
        for r in critical:
            txt += f"  • {_fmt(r.get('street', '?'), r.get('lat'), r.get('lon'))} - {r.get('status', '?')}\n"
        txt += "\n"
    
    if high:
        txt += "⚠️ PERTURBATIONS:\n"
        for r in high:
            txt += f"  • {_fmt(r.get('street', '?'), r.get('lat'), r.get('lon'))} - {r.get('status', '?')}\n"
        txt += "\n"
    
    if medium:
        txt += "📍 DENSE:\n"
        for r in medium[:5]:
            txt += f"  • {_fmt(r.get('street', '?'), r.get('lat'), r.get('lon'))} - {r.get('status', '?')}\n"
        if len(medium) > 5:
            txt += f"  ... et {len(medium)-5} autres zones denses\n"
    
    txt += f"\n💡 {len(roads)} axe(s) perturbé(s) actuellement"
    return txt


def format_parking_results(mcp_result: dict) -> str:
    """Formate les données de parkings Rennes pour le LLM"""

    data = mcp_result.get("result", {})

    if not data.get("success"):
        return f"❌ Erreur parkings: {data.get('error', 'Erreur inconnue')}"

    parkings = data.get("parkings", [])
    updated = data.get("updated", "maintenant")

    if not parkings:
        return f"⚠️ Aucune donnée de parking disponible (mis à jour à {updated})"

    txt = f"🅿️ Parkings à Rennes ({updated}):\n\n"

    # Afficher top 10 parkings avec le plus de places disponibles
    for p in parkings[:10]:
        txt += f"• {p['name']}\n"
        txt += f"  {p['status']} - {p['available']}/{p['total']} places\n"
        if p.get('location'):
            txt += f"  📍 {p['location']}\n"
        
        # Afficher les tarifs si disponibles
        if p.get('pricing'):
            tarifs_str = ", ".join([f"{duree}: {prix}" for duree, prix in p['pricing'].items()])
            txt += f"  💰 Tarifs: {tarifs_str}\n"
        
        txt += "\n"

    txt += f"💡 {len(parkings)} parking(s) surveillés"
    return txt


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        print(f"📨 Message reçu: {request.message}")

        # 1. MCP – détection + exécution
        mcp_result = mcp.process_message(request.message)
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

        # 3. Scraping de page web si URL
        else:
            import re
            urls = re.findall(r"https?://[^\s]+", request.message)
            if urls:
                scraped = scrape_url(urls[0])
                if scraped.get("success"):
                    context = (
                        f"Données scrapées de {urls[0]}:\n"
                        f"Titre: {scraped.get('title')}\n"
                        f"Contenu: {scraped.get('content')[:1500]}"
                    )

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

@app.get("/api/traffic")
async def get_traffic():
    """Endpoint dédié pour l'état du trafic"""
    try:
        result = mcp.execute_tool("get_traffic_status", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parkings")
async def get_parkings():
    """Endpoint dédié pour la disponibilité des parkings"""
    try:
        result = mcp.execute_tool("get_parking_status", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
