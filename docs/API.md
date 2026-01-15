# Documentation API - FuelBot Backend

## 🌐 Base URL
```
http://127.0.0.1:8000
```

---

## Endpoints

### 1. **POST /api/chat**
Point d'entrée principal pour envoyer un message à l'assistant.

#### Request
```json
{
  "message": "Prix du SP95",
  "latitude": 48.1104,
  "longitude": -1.6769,
  "history": []
}
```

#### Parameters
| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `message` | string | ✅ | Question de l'utilisateur |
| `latitude` | float | ❌ | Latitude GPS (optionnel) |
| `longitude` | float | ❌ | Longitude GPS (optionnel) |
| `history` | array | ❌ | Historique conversation (vide par défaut) |

#### Response - Success (200)
```json
{
  "response": "Voici les stations SP95 les moins chères...",
  "tool_used": "search_fuel_prices",
  "data": [
    {
      "ville": "Rennes",
      "adresse": "238 Rue Saint-Malo",
      "cp": "35000",
      "fuel_type": "SP95",
      "price": 1.681,
      "distance_km": 2.3,
      "updated": "2025-12-30T14:26:28"
    }
  ],
  "context": "⛽ 2 stations pour SP95..."
}
```

#### Response - Sans outil détecté (200)
```json
{
  "response": "🚗 Je suis un assistant mobilité Rennes...",
  "tool_used": null,
  "data": null
}
```

#### Response - Error (500)
```json
{
  "detail": "Message d'erreur"
}
```

---

### 2. **GET /api/health**
Vérification de l'état du serveur.

#### Response (200)
```json
{
  "status": "ok",
  "api": "api.ia.epitech.bzh",
  "model": "qwen3:30b",
  "mcp_tools": [
    "search_fuel_prices",
    "get_cheapest_station",
    "compare_fuel_prices",
    "get_fuel_stats",
    "get_traffic_status",
    "get_parking_status",
    "estimate_drive_time",
    "scrape_website"
  ]
}
```

---

## 🛠️ Outils MCP Disponibles

### ⛽ **Carburant**

#### `search_fuel_prices`
Recherche les prix de carburant dans une ville ou code postal.

**Déclencheurs** :
- "prix gazole"
- "essence Rennes"
- "SP95 35000"

**Paramètres extraits** :
```python
{
  "ville": "Rennes",
  "fuel_type": "SP95",
  "limit": 5
}
```

#### `get_cheapest_station`
Trouve les stations les moins chères.

**Déclencheurs** :
- "station la moins chère"
- "prix le plus économique"
- "pas cher gazole"

#### `get_fuel_stats`
Statistiques globales sur les prix.

**Déclencheurs** :
- "moyenne prix gazole"
- "statistiques carburant"

---

### 🅿️ **Parking**

#### `get_parking_status`
Disponibilité des parkings à Rennes.

**Déclencheurs** :
- "parking disponible"
- "places de stationnement"
- "se garer Rennes"

**Response data** :
```json
[
  {
    "name": "Parking République",
    "status": "Ouvert",
    "available": 42,
    "total": 400,
    "distance_km": 1.2,
    "pricing": {
      "1h": "2.00€",
      "3h": "5.50€"
    }
  }
]
```

---

### 🚦 **Trafic**

#### `get_traffic_status`
État du trafic sur Rennes Métropole.

**Déclencheurs** :
- "état du trafic"
- "bouchons Rennes"
- "circulation rocade"

**Response** :
```json
{
  "global_status": "fluide",
  "incidents": [],
  "affected_roads": [],
  "last_update": "2026-01-15T14:30:00"
}
```

---

### 🚗 **Trajet**

#### `estimate_drive_time`
Estimation du temps de trajet avec trafic.

**Déclencheurs** :
- "temps de trajet République à Cesson"
- "combien de temps pour aller de X à Y"
- "distance Rennes centre à gare"

**Paramètres** :
```python
{
  "origin_name": "Rennes Centre",
  "destination_name": "Cesson-Sévigné",
  "user_location": (48.1104, -1.6769)  # Si fourni
}
```

**Response** :
```json
{
  "success": true,
  "origin": [48.1113, -1.68],
  "destination": [48.1204, -1.6333],
  "distance_km": 8.5,
  "duration_base_minutes": 15.0,
  "traffic_impact_minutes": 5,
  "duration_estimated_minutes": 20.0,
  "affected_roads": ["Rocade Sud"]
}
```

---

## 🔐 CORS

Le backend autorise **toutes les origines** en développement :

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ À restreindre en production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**⚠️ Production** : Restreindre à votre domaine :
```python
allow_origins=["https://votre-domaine.com"]
```

---

## 📍 Calcul de Distance GPS

Quand `latitude` et `longitude` sont fournis, le backend calcule automatiquement la distance entre l'utilisateur et chaque résultat (stations, parkings).

**Formule utilisée** : Haversine
```python
distance_km = calculate_distance(
    user_lat, user_lon,
    station_lat, station_lon
)
```

**Ajouté dans les résultats** :
```json
{
  "adresse": "238 Rue Saint-Malo",
  "distance_km": 2.3  // ← Calculé automatiquement
}
```

---

## 🧪 Exemples d'Utilisation

### cURL
```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Prix du gazole",
    "latitude": 48.1104,
    "longitude": -1.6769
  }'
```

### Python
```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/chat",
    json={
        "message": "Parking disponible",
        "latitude": 48.1104,
        "longitude": -1.6769
    }
)

data = response.json()
print(data["response"])
```

### JavaScript (Frontend)
```javascript
const response = await fetch("http://127.0.0.1:8000/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: "État du trafic",
    latitude: 48.1104,
    longitude: -1.6769
  })
});

const data = await response.json();
console.log(data.response);
```
