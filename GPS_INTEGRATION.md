# 📍 Guide d'Intégration GPS - Assistant Mobilité Rennes

## Vue d'ensemble

L'application utilise la **géolocalisation du navigateur** pour permettre aux utilisateurs de faire des requêtes relatives à leur position actuelle.

### Objectifs
- Calculer des itinéraires depuis la position GPS de l'utilisateur
- Support de 147 lieux emblématiques de Rennes Métropole
- Tolérance aux typos avec fuzzy matching
- Fallback gracieux si GPS indisponible

### Exemples de requêtes supportées
- "Combien de temps pour aller à la gare **en partant de ma position** ?"
- "Temps pour aller à l'université Rennes 2 **depuis ma position**"
- "Aller à la place Saint-Anne **d'ici**"
- "Distance jusqu'au CHU **où je suis**"

---

## Architecture GPS

### Frontend (HTML/CSS/JavaScript)

#### Récupération automatique de la position

```javascript
// script.js
let userLocation = null;

function getUserLocation() {
  if (!navigator.geolocation) {
    console.warn("❌ Geolocation non supportée - utilisant position par défaut");
    // Fallback: Rennes centre
    userLocation = { lat: 48.1104, lon: -1.6769 };
    return;
  }

  // Timeout après 5 secondes
  const timeoutId = setTimeout(() => {
    console.warn("⚠️ Geolocation timeout (>5s) - utilisant fallback");
    if (!userLocation) {
      userLocation = { lat: 48.1104, lon: -1.6769 };
    }
  }, 5000);

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      clearTimeout(timeoutId);
      userLocation = {
        lat: pos.coords.latitude,      // Latitude (e.g., 48.1150)
        lon: pos.coords.longitude      // Longitude (e.g., -1.6700)
      };
      console.log("✓ Position GPS acquise:", userLocation);
    },
    (err) => {
      clearTimeout(timeoutId);
      console.warn("⚠️ Geolocation refusée:", err.message);
      // Fallback si refus utilisateur
      if (!userLocation) {
        userLocation = { lat: 48.1104, lon: -1.6769 };
        console.log("📍 Position fallback utilisée:", userLocation);
      }
    },
    { 
      timeout: 5000,
      enableHighAccuracy: false
    }
  );
}

// Appelé automatiquement au chargement
getUserLocation();
```
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    history: list = Field(default_factory=list)
    latitude: Optional[float] = Field(default=None)    # ← GPS
    longitude: Optional[float] = Field(default=None)   # ← GPS
const response = await fetch("http://127.0.0.1:8000/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: query,
    history: [],
    latitude: userLocation ? userLocation.lat : null,
    longitude: userLocation ? userLocation.lon : null
  }),
});
```

### Backend (FastAPI + MCP)

#### 1. Réception des coordonnées GPS

**app/main.py - ChatRequest**
```python
class ChatRequest(BaseModel):
    message: str
    history: list = Field(default_factory=list)
    latitude: float = Field(default=None)    # ← Nouvelle
    longitude: float = Field(default=None)   # ← Nouvelle

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Construction du tuple GPS
    user_location = (request.latitude, request.longitude) \
        if request.latitude and request.longitude else None
    
    # Passage au MCP
    mcp_result = mcp.process_message(
        request.message,
        user_location=user_location  # ← Nouvellement supporté
    )
    # ...
```

#### 2. Traitement dans le MCP

**app/mcp_sim.py - process_message()**
```python
def process_message(self, message: str, user_location: tuple = None) -> Dict[str, Any]:
    """
    Process complet: détecte l'outil, extrait les params, et exécute
    
    Args:
        message: Le message utilisateur
        user_location: Tuple (latitude, longitude) de la position GPS utilisateur
    """
    tool_name = self.detect_tool_needed(message)
    
    if not tool_name:
        return {"tool": None}
    
    params = self._extract_params_from_message(message, tool_name)
    
    # Ajouter la position utilisateur si disponible et pertinente
    if user_location and tool_name == 'estimate_drive_time':
        params['user_location'] = user_location  # ← Clé GPS passée
    
    result = self.execute_tool(tool_name, params)
    
    return {
        "tool": tool_name,
        "params": params,
        "result": result
    }
```

#### 3. Extraction et reconnaissance de "ma position"

**app/mcp_sim.py - _extract_params_from_message()**

Le système reconnaît les phrases contenant "ma position" :

```python
if tool_name == 'estimate_drive_time':
    # Déterminer si "ma position" est mentionnée
    has_my_position = any(phrase in message_lower for phrase in [
        'ma position',        # "en partant de ma position"
        'position actuelle',  # "depuis la position actuelle"
        'où je suis',         # "combien de temps où je suis"
        'ici',                # "aller d'ici à..."
        'd\'ici',             # "d'ici jusqu'à..."
        'depuis d\'ici'       # "depuis d'ici"
    ])
    
    # Variante 3: "pour aller à X en partant de ma position"
    if 'origin_name' not in params and has_my_position:
        pattern_en_partant = r'aller\s+à\s+(.+?)\s+en\s+partant'
        m = re.search(pattern_en_partant, message)
        if m:
            params['origin_name'] = 'ma position'  # ← Marqueur spécial
            params['destination_name'] = m.group(1).strip()
```

#### 4. Utilisation de la position GPS

**app/mcp_sim.py - _estimate_drive_time()**

```python
def _estimate_drive_time(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Estime le temps de trajet en tenant compte du trafic"""
    
    origin_name = params.get('origin_name', 'Rennes Centre')
    destination_name = params.get('destination_name', 'Rennes')
    user_location = params.get('user_location')  # ← GPS utilisateur
    
    # Si l'origine est "ma position", utiliser les coordonnées GPS
    if user_location and origin_name.lower() in [
        'ma position', 'position actuelle', 'où je suis', 'ici'
    ]:
        origin_coords = user_location
        print(f"[DRIVE TIME] Utilisant position GPS de l'utilisateur: {origin_coords}")
    else:
        # Sinon, rechercher dans la base de données
        origin_coords = find_location(origin_name)
        if not origin_coords:
            suggestions = get_suggestions(origin_name, limit=3)
            return {
                "error": f"Lieu de départ '{origin_name}' inconnu."
            }
    
    # Trouver la destination dans la base de données
    dest_coords = find_location(destination_name)
    if not dest_coords:
        suggestions = get_suggestions(destination_name, limit=3)
        return {
            "error": f"Lieu d'arrivée '{destination_name}' inconnu."
        }
    
    # Calculer l'itinéraire
    result = self.drive_time_estimator.estimate_drive_time(
        origin_coords, dest_coords
    )
   Détection des variantes "ma position"

Le système reconnaît plusieurs formulations grâce à 6 variantes d'extraction dans `param_extractor.py` :

### Variantes supportées

**Variante 1 :** "combien de temps pour aller à X"
```python
pattern = r'(?:combien de temps|temps)\s+pour\s+aller\s+(?:à|vers|au)\s+([^\s,?.!]+(?:\s+[^\s,?.!]+)*?)(?:\s|$|\?)'
# Exemple: "combien de temps pour aller à la gare"
# Capture: destination = "la gare"
```

**Variante 2 :** "aller à X depuis ma position"
```python
pattern = r'aller\s+(?:à|vers|au)\s+(.+?)\s+depuis'
# Exemple: "aller à rennes 2 depuis ma position"
# Capture: destination = "rennes 2", origin = "ma position"
```

**Variante 3 :** "aller à X en partant de ma position"
```python
pattern = r'aller\s+à\s+(.+?)\s+en\s+partant'
# Exemple: "aller à la gare en partant de ma position"
# Capture: destination = "la gare", origin = "ma position"
```

**Variante 4 :** "de X à Y" ou "X vers Y"
```python
pattern_de_a = r'(?:de|depuis)\s+(.+?)\s+(?:à|vers|jusqu\'à)\s+(.+?)(?:\s|$|\?)'
# Exemple: "de ma position à la gare"
# Capture: origin = "ma position", destination = "la gare"
```

**Variante 5 :** "temps X Y"
```python
pattern = r'temps\s+(\S+)\s+(\S+)'
# Exemple: "temps gare villejean"
# Capture: origin = "gare", destination = "villejean"
```

**Variante 6 :** "aller X" (simple, sans préposition)
```python
pattern = r'(?:aller|rendre)\s+([^\s?,!.]+(?:\s+[^\s?,!.]+){0,3})'
# Exemple: "aller gare"
# Capture: destination = "gare"
```

### Phrases déclencheuses

Le système détecte automatiquement "ma position" via ces mots-clés :
```python
position_keywords = [
    'ma position',
    'position actuelle',
    'où je suis',
    'ici',
    'd\'ici',
    'depuis d\'ici'
]

has_my_position = any(phrase in message_lower for phrase in position_keywords)
```

---

##  return result
```

## Base de données de localisations

**app/rennes_locations.py** - Contient 100+ lieux de Rennes Métropole :

```python
RENNES_LOCATIONS = {
    'rennes centre': (48.1113, -1.6800),
    'la gare': (48.1039, -1.6720),
    'université rennes 2': (48.1206, -1.6700),
    'place saint anne': (48.1103, -1.6780),
    'mail françois mitterrand': (48.1100, -1.6800),
    # ... 100+ entrées
}

def find_location(name: str):
    """Recherche une localisation par nom (case-insensitive)"""
    name_lower = name.lower().strip()
    for loc_name, coords in RENNES_LOCATIONS.items():
        if name_lower == loc_name:
            return coords
    return None

def get_suggestions(partial_name: str, limit=3):
    """Retourne les suggestionss proches (fuzzy match)"""
    # Implémentation via difflib
    pass
```

## Exemple d'utilisation

### Requête avec GPS

**Frontend envoie :**
```json
{
  "message": "combien de temps pour aller à la gare en partant de ma position ?",
  "latitude": 48.1150,
  "longitude": -1.6700
}
```

**Processus backend :**
1. Dests et Validation

### Tests unitaires
Voir `tests/unit/test_param_extractor.py` pour valider les 6 variantes :

```python
def test_variante_1_simple():
    # "combien de temps pour aller à la gare"
    assert params['destination_name'] == 'la gare'

def test_variante_2_depuis():
    # "aller à rennes 2 depuis ma position"
    assert params['destination_name'] == 'rennes 2'
    assert params['origin_name'] == 'ma position'
```

### Tests d'intégration
Voir `tests/integration/test_gps_e2e.py` pour tests end-to-end complets :

```python
def test_gps_position_detection():
    result = mcp.process_message(
        "combien de temps pour aller à la gare depuis ma position",
        user_location=(48.1104, -1.6769)
    )
    assert result['result']['success'] == True
    assert result['result']['distance_km'] > 0
```

---

## Tétecte l'outil : `estimate_drive_time` ✓
2. Extrait les paramètres :
   - `origin_name`: "ma position" ← Reconnu
   - `destination_name`: "gare" ← Extrait
3. Résout les coordonnées :
   - Origine : (48.1150, -1.6700) ← De l'utilisateur
   - Destination : (48.1039, -1.6720) ← De la base de données
4. Calcule l'itinéraire :
   - Distance : 2.91 km
   - Durée estimée : 7.7 minutes

**Réponse retournée :**
```json
{
  "tool": "estimate_drive_time",
  "result": {
    "success": true,
    "origin": [48.1150, -1.6700],
    "destination": [48.1039, -1.6720],
    "distance_km": 2.91,
    "duration_estimated_minutes": 7.7,
    "affected_roads": [],
    "warning": "Trafic non disponible"
  }
}
```

## Déploiement & Permissions

### Permissions requises

1. **Navigateur demande la permission :**
   - L'utilisateur doit autoriser la géolocalisation
   - Popup : "Le site demande accès à votre position"

2. **HTTPS en production :**
   - Geolocation API nécessite HTTPS (sauf localhost)
   - Configuration : voir section HTTPS du README principal

3. **Privacy :**
   - Position stockée **EN LOCAL** (RAM du navigateur)
   - Envoyée **À CHAQUE REQUÊTE** à l'API
   - **Pas de stockage** en base de données

### Configuration serveur

Si le frontend est sur HTTPS, le backend doit aussi être en HTTPS ou répondre depuis le même domaine (voir CORS).

```bash
# Development (localhost - pas de restriction)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production (HTTPS recommandé)
uvicorn app.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem --host 0.0.0.0 --port 8000
```

## Variantes supportées

Le système reconnaît plusieurs formulations de requêtes GPS :

```
✓ "combien de temps pour aller à la gare en partant de ma position ?"
✓ "temps pour aller à l'université Rennes 2 depuis ma position"
✓ "aller à la place Saint Anne depuis ma position"
✓ "parking disponible près de chez moi"  (futur)
✓ "stations essence d'ici"  (futur)
✓ "trafic où je suis"  (futur)
```

## Troubleshooting

### ❌ "Autorise la géolocalisation"

**Problème :** L'alerte s'affiche constamment
**Solution :**
1. Vérifier les permissions du navigateur
2. Chrome/Firefox : Paramètres → Confidentialité → Permissions → Localisation
3. Autoriser le site
4. Relancer le navigateur

### ❌ "Position non utilisée"

**Problème :** GPS reçu mais pas utilisé dans les calculs
**Solution :**
1. Vérifier la console (F12) pour voir si position est capturée
2. Ajouter "en partant de ma position" ou "depuis ma position" à la requête
3. Le système ne reconnaît que ces phrases précises

### ❌ "Lieu d'arrivée inconnu"

**Problème :** "Gare" ou autre lieu n'est pas reconnu
**Solution :**
1. Consulter `app/rennes_locations.py` pour voir les lieux disponibles
2. Ajouter nouveaux lieux si manquants
3. Utiliser des noms connus : "la gare", "université Rennes 2", "place Saint Anne"

## Performance

- **Latence GPS :** ~100-500ms (selon le navigateur/OS)
- **Calcul itinéraire :** ~1-2s (appel OSRM)
- **Latence totale :** ~2-3s depuis le clic utilisateur

## Futures améliorations

- [ ] Support du parking avec position actuelle
- [ ] Stations-service proches (radius search)
- [ ] Alertes trafic en temps réel avec GPS
- [ ] Historique des trajets récents
- [ ] Prédiction ETA vs temps réel

---

**Questions ?** Consulte [README.md](README.md) pour l'architecture globale.
