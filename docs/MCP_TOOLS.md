# Outils MCP - Documentation Technique

## 🧰 Vue d'ensemble

Le système MCP (Model Context Protocol) simule un système d'outils permettant au LLM d'interagir avec des sources de données externes (APIs, scraping, calculs).

---

## 🔄 Processus MCP

```
User Message
    │
    ▼
┌────────────────┐
│ Tool Detector  │  ← Détecte quel outil utiliser
└───────┬────────┘
        │
        ▼
┌────────────────┐
│Param Extractor │  ← Extrait les paramètres du message
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Tool Executor  │  ← Exécute l'outil + calcul GPS
└───────┬────────┘
        │
        ▼
    Résultat JSON
```

---

## 1️⃣ Tool Detector (`tool_detector.py`)

### Principe
Détection par **mots-clés** avec analyse du message utilisateur.

### Mots-clés par catégorie

#### ⛽ Carburant
```python
fuel_keywords = [
    'gazole', 'essence', 'carburant', 'sp95', 'sp98', 
    'e10', 'e85', 'station', 'prix', 'moins cher', 
    'pas cher', 'economique'
]
```

#### 🅿️ Parking
```python
parking_keywords = [
    'parking', 'parkings', 'stationner', 'stationnement',
    'place', 'places', 'garer', 'garage', 'park'
]
```

#### 🚦 Trafic
```python
traffic_keywords = [
    'traffic', 'bouchons', 'congestion', 'embouteillage',
    'circulation', 'route', 'autoroute', 'ralentissement',
    'accident'
]
```

#### 🚗 Trajet
```python
drive_keywords = [
    'temps', 'trajet', 'combien de temps', 'temps de route',
    'duree', 'aller a', 'me rendre', 'distance', 'km'
]
```

### Logique de détection

```python
def detect(self, user_message: str) -> Optional[str]:
    # 1. Normalisation
    message = remove_accents(message.lower())
    
    # 2. Carburant (priorité haute si keywords match)
    if any(kw in message for kw in fuel_keywords):
        if 'moins cher' in message:
            return "get_cheapest_station"
        else:
            return "search_fuel_prices"
    
    # 3. Trajet (si pattern "de X à Y")
    if pattern_trajet(message):
        return "estimate_drive_time"
    
    # 4. Trafic
    if any(kw in message for kw in traffic_keywords):
        return "get_traffic_status"
    
    # 5. Parking
    if any(kw in message for kw in parking_keywords):
        return "get_parking_status"
    
    return None  # Aucun outil détecté
```

### ⚠️ Limitations actuelles

1. **Chevauchement de mots-clés**
   - "parking autour de Université" → match "de" (trajet) avant "parking"
   - Solution actuelle : ordre de priorité dans les if/else

2. **Pas de contexte sémantique**
   - "Je cherche pas cher" → détecte carburant même si c'est un parking

3. **Pas de gestion multi-intentions**
   - "Prix gazole et parking disponible" → détecte seulement le premier

---

## 2️⃣ Param Extractor (`param_extractor.py`)

### Principe
Extrait les paramètres nécessaires du message selon l'outil détecté.

### Extraction par outil

#### Carburant
```python
{
    "fuel_type": "SP95",      # Détecté: sp95, gazole, e10...
    "ville": "Rennes",         # Extrait du message
    "code_postal": "35000",    # Ou code postal si présent
    "limit": 5                 # Par défaut
}
```

**Patterns utilisés** :
```python
# Type carburant
r'\b(gazole|sp95|sp98|e10|e85)\b'

# Ville
r'\bà\s+(\w+)'
r'\b(?:ville|dans|sur)\s+(\w+)'

# Code postal
r'\b(35\d{3})\b'
```

#### Parking
```python
{
    "location": "Centre-ville",  # Si précisé
    "limit": 5
}
```

#### Trajet
```python
{
    "origin_name": "Rennes Centre",
    "destination_name": "Cesson-Sévigné",
    "user_location": None  # Ajouté si GPS fourni
}
```

**Patterns utilisés** :
```python
# Pattern "de X à Y"
r'de\s+(.+?)\s+(?:a|à)\s+(.+?)(?:\s|$)'

# Pattern "X vers Y"
r'(.+?)\s+vers\s+(.+?)(?:\s|$)'
```

---

## 3️⃣ Tool Executor (`tool_executor.py`)

### Principe
Exécute l'outil détecté avec enrichissement GPS.

### Workflow

```python
def execute(tool_name, params, user_location=None):
    # 1. Appel scraper/outil
    results = tool_method(params)
    
    # 2. Enrichissement GPS si position fournie
    if user_location:
        for result in results:
            station_coords = get_station_coords(result)
            distance = calculate_distance(
                user_location[0], user_location[1],
                station_coords[0], station_coords[1]
            )
            result['distance_km'] = distance
    
    # 3. Retour JSON
    return {
        "success": True,
        "results": results
    }
```

### Calcul de distance GPS

**Formule Haversine** (distance orthodromique) :

```python
def calculate_distance(lat1, lon1, lat2, lon2) -> float:
    R = 6371  # Rayon Terre en km
    
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    a = sin(dlat/2)² + cos(lat1) * cos(lat2) * sin(dlon/2)²
    c = 2 * asin(sqrt(a))
    
    distance = R * c
    return round(distance, 1)
```

**Exemple** :
```python
distance = calculate_distance(
    48.1104, -1.6769,  # User (Rennes centre)
    48.1204, -1.6333   # Station (Cesson)
)
# → 5.2 km
```

---

## 🔧 Scrapers / Data Sources

### Fuel Scraper (`fuel_scraper.py`)
- **Source** : https://donnees.roulez-eco.fr/opendata/jour
- **Format** : ZIP → XML
- **Cache** : 24h local JSON
- **Filtrage** : Ille-et-Vilaine (35) uniquement

```python
class FuelPriceScraper:
    def fetch_daily_prices() -> Dict
    def search_by_city(ville, fuel_type) -> List[Dict]
    def search_by_postal_code(cp, fuel_type) -> List[Dict]
    def get_cheapest_in_city(ville, fuel_type, limit) -> List[Dict]
```

### Parking Scraper (`parking_scraper.py`)
- **Source** : API Rennes Métropole (data.rennesmetropole.fr)
- **Endpoint** : `/api/records/1.0/search/?dataset=etat-des-parkings-en-temps-reel`
- **Temps réel** : Oui

### Traffic Scraper (`traffic_scraper.py`)
- **Source** : API Rennes Métropole (trafic en temps réel)
- **Données** : Incidents, ralentissements, fermetures

### Drive Time Estimator (`drive_time_estimator.py`)
- **Calcul** : Distance GPS + vitesse moyenne
- **Enrichissement** : État du trafic si disponible

---

## 🎯 Améliorations Possibles

### 1. Détection par LLM
```python
def detect_with_llm(message: str) -> str:
    prompt = f"""
    Classifie cette demande:
    - parking
    - carburant
    - trafic
    - trajet
    
    Message: {message}
    Réponse (un mot):
    """
    return llm.generate(prompt)
```

### 2. Multi-tool detection
Gérer plusieurs outils dans une requête :
```
"Prix gazole et parking disponible"
→ [search_fuel_prices, get_parking_status]
```

### 3. Entity extraction
```python
entities = extract_entities(message)
# {
#   "action": "trouver",
#   "type": "parking",
#   "location": "Université Rennes 2"
# }
tool = map_entities_to_tool(entities)
```

### 4. Cache intelligent
- Cache géolocalisé (résultats par position)
- TTL adaptatif selon l'outil
- Invalidation sélective
