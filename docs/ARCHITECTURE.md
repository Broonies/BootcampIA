# Architecture Technique - FuelBot Assistant

## 📐 Vue d'ensemble

FuelBot est un assistant IA de mobilité pour Rennes Métropole, composé de trois couches principales :

```
┌─────────────────────────────────────────┐
│         Frontend (HTML/JS/CSS)          │
│  - Interface utilisateur                │
│  - Géolocalisation GPS                  │
│  - Affichage des résultats              │
└──────────────┬──────────────────────────┘
               │ HTTP/JSON
               │ (POST /api/chat)
┌──────────────▼──────────────────────────┐
│         Backend (FastAPI/Python)        │
│  - API REST                             │
│  - LLM Service (Ollama)                 │
│  - MCP Simulator                        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        Couche Outils (MCP Tools)        │
│  - Scraping données carburant           │
│  - Scraping trafic                      │
│  - Scraping parking                     │
│  - Calcul de trajets                    │
└─────────────────────────────────────────┘
```

---

## 🏗️ Structure du Projet

```
BootcampIA/
├── backend/
│   └── app/
│       ├── main.py              # Point d'entrée FastAPI
│       ├── llm.py               # Service LLM (Ollama)
│       ├── mcp_sim.py           # Simulateur MCP
│       ├── tool_detector.py     # Détection d'outils par mots-clés
│       ├── param_extractor.py   # Extraction de paramètres
│       ├── tool_executor.py     # Exécution des outils
│       ├── formatters.py        # Formatage des résultats
│       ├── models.py            # Modèles Pydantic
│       ├── config.py            # Configuration
│       ├── rennes_locations.py  # Base de données lieux Rennes
│       └── tools/
│           ├── fuel_scraper.py           # Scraping carburant
│           ├── parking_scraper.py        # Scraping parking
│           ├── traffic_scraper.py        # Scraping trafic
│           ├── route_scraper.py          # Scraping itinéraires
│           └── drive_time_estimator.py   # Estimation temps trajet
├── frontend/
│   ├── index.html               # Interface HTML
│   ├── script.js                # Logique frontend
│   └── styles.css               # Styles UI
├── cache/                        # Cache données
├── tests/                        # Tests unitaires & intégration
└── docs/                         # Documentation (ce dossier)
```

---

## 🔄 Flux de Données

### 1. **Frontend → Backend**
```javascript
// Envoi requête HTTP POST
fetch("http://127.0.0.1:8000/api/chat", {
  method: "POST",
  body: JSON.stringify({
    message: "Prix du SP95",
    latitude: 48.1104,
    longitude: -1.6769,
    history: []
  })
})
```

### 2. **Backend : Traitement MCP**
```python
# 1. Détection outil (tool_detector.py)
tool = detect("Prix du SP95")  # → "search_fuel_prices"

# 2. Extraction paramètres (param_extractor.py)
params = extract(message, tool)  # → {fuel_type: "SP95"}

# 3. Exécution outil (tool_executor.py)
result = execute(tool, params, user_location)

# 4. Calcul distances GPS (si position fournie)
distance = calculate_distance(user_lat, user_lon, station_lat, station_lon)
```

### 3. **Backend → LLM → Frontend**
```python
# Formatage contexte pour LLM
context = format_fuel_results(result)

# Appel LLM
response = llm.chat(message, context)

# Réponse JSON
return {
  "response": "Voici les stations...",
  "tool_used": "search_fuel_prices",
  "data": [stations avec distance_km]
}
```

---

## 🧩 Composants Clés

### **MCP Simulator** (`mcp_sim.py`)
Orchestrateur principal qui coordonne :
- Détection d'outil
- Extraction de paramètres
- Exécution avec position GPS

### **Tool Detector** (`tool_detector.py`)
Détection par mots-clés (4 catégories) :
- 🅿️ Parking
- 🚦 Trafic
- ⛽ Carburant
- 🚗 Trajet

**⚠️ Problème actuel** : Chevauchement des mots-clés (ex: "autour de" match trajet ET parking)

### **Tool Executor** (`tool_executor.py`)
Exécute les outils et enrichit avec :
- Calcul de distances GPS (formule Haversine)
- Tri par pertinence
- Limitation résultats (5 par défaut)

### **LLM Service** (`llm.py`)
- Modèle : `qwen3:30b` via Ollama
- Contexte verrouillé (mobilité Rennes uniquement)
- Température : 0.3 (peu créatif)

---

## 🔧 Technologies

| Couche | Technologie |
|--------|-------------|
| Backend | FastAPI, Python 3.13 |
| Frontend | HTML5, Vanilla JS, CSS3 |
| LLM | Ollama (qwen3:30b) |
| Data | XML scraping, JSON cache |
| API | REST, CORS activé |
| GPS | Haversine distance formula |

---

## 🚀 Déploiement

### Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
python -m http.server 3000
# Ou ouvrir directement index.html
```

---

## 📊 Endpoints API

Voir [API.md](./API.md) pour la documentation complète des endpoints.
