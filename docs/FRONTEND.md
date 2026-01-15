# Documentation Frontend - FuelBot UI

## 📱 Technologies
- HTML5
- Vanilla JavaScript (ES6+)
- CSS3 (Flexbox, Grid)
- Geolocation API

---

## 🗂️ Structure

```
frontend/
├── index.html      # Structure HTML
├── script.js       # Logique application
└── styles.css      # Styles et animations
```

---

## 🎨 Interface Utilisateur

### Composants Principaux

#### 1. **Header**
```html
<div class="header">
  <div class="header-icon">⛽</div>
  <div class="header-info">
    <h1>FuelBot Assistant</h1>
    <p>L'assistant IA dédié pour les conducteurs à Rennes !</p>
  </div>
</div>
```

#### 2. **Chat Messages**
Zone scrollable affichant :
- Messages utilisateur (alignés droite, fond bleu)
- Messages IA (alignés gauche, fond gris)
- Cartes de résultats (stations, parkings)

#### 3. **Input Area**
```html
<div class="input-area">
  <input type="text" id="userInput" placeholder="..." />
  <button id="sendBtn" onclick="sendMessage()">➤</button>
</div>
```

#### 4. **Suggestions Chips**
```html
<div class="suggestion-chip" onclick="sendSuggestion('Prix du SP95')">
  Prix du SP95
</div>
```

---

## 🧩 Composants JavaScript

### 1. Géolocalisation GPS

```javascript
let userLocation = null;

function getUserLocation() {
  if (!navigator.geolocation) {
    // Fallback: Rennes centre
    userLocation = { lat: 48.1104, lon: -1.6769 };
    return;
  }
  
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      userLocation = {
        lat: pos.coords.latitude,
        lon: pos.coords.longitude
      };
      console.log("✓ Position GPS acquise:", userLocation);
    },
    (err) => {
      console.warn("⚠️ GPS refusé, fallback Rennes");
      userLocation = { lat: 48.1104, lon: -1.6769 };
    },
    { timeout: 5000 }
  );
}

// Appel au chargement
getUserLocation();
```

**Fallback** : Si GPS refusé → Position Rennes centre par défaut

---

### 2. Envoi Message Backend

```javascript
async function sendToBackend(query) {
  const response = await fetch("http://127.0.0.1:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: query,
      history: [],
      latitude: userLocation?.lat || null,
      longitude: userLocation?.lon || null
    })
  });
  
  const data = await response.json();
  return processResponse(data);
}
```

**Flow** :
1. Récupère position GPS (si disponible)
2. Envoie requête POST au backend
3. Traite la réponse JSON

---

### 3. Traitement des Réponses

```javascript
function processResponse(data) {
  // Cas 1: Données structurées (stations/parkings)
  if (data.data && Array.isArray(data.data) && data.data.length > 0) {
    const isParking = data.data[0].available !== undefined;
    
    if (isParking) {
      return {
        type: "parkings",
        parkings: formatParkings(data.data)
      };
    } else {
      return {
        type: "stations",
        stations: formatStations(data.data)
      };
    }
  }
  
  // Cas 2: Réponse textuelle simple
  return {
    type: "text",
    text: data.response
  };
}
```

---

### 4. Création Cartes Stations

```javascript
function createStationCard(station) {
  const card = document.createElement("div");
  card.className = "station-card";
  
  card.innerHTML = `
    <div class="station-header">
      <div class="station-name">${station.name}</div>
      <div class="station-distance">${station.distance}</div>
    </div>
    <div class="fuel-prices">
      ${station.prices.map(p => `
        <div class="fuel-price">
          <div class="fuel-type">${p.type}</div>
          <div class="price">${p.price} €/L</div>
        </div>
      `).join("")}
    </div>
    ${station.best ? '<div class="best-price">Meilleur prix</div>' : ""}
  `;
  
  return card;
}
```

**Données attendues** :
```javascript
{
  name: "238 Rue Saint-Malo, Rennes",
  distance: "2.3 km",  // ← Calculé par backend
  best: true,
  prices: [
    { type: "SP95", price: "1.681" }
  ]
}
```

---

### 5. Création Cartes Parkings

```javascript
function createParkingCard(parking) {
  const card = document.createElement("div");
  card.className = "station-card";
  
  card.innerHTML = `
    <div class="station-header">
      <div class="station-name">${parking.name}</div>
      <div class="station-distance">${parking.distance}</div>
    </div>
    <div class="station-info">
      <div>${parking.status}</div>
      <div>${parking.available}/${parking.total} places</div>
    </div>
    ${pricingHTML}
  `;
  
  return card;
}
```

---

### 6. Indicateur de Saisie

```javascript
function createTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "message ai-message";
  
  const indicator = document.createElement("div");
  indicator.className = "typing-indicator active";
  indicator.innerHTML = `
    <span class="dot"></span>
    <span class="dot"></span>
    <span class="dot"></span>
  `;
  
  wrapper.appendChild(indicator);
  return wrapper;
}
```

**Animation CSS** : 3 points qui apparaissent séquentiellement

---

## 🎨 Styles CSS

### Variables
```css
:root {
  --primary-color: #4a90e2;
  --secondary-color: #f5f5f5;
  --text-color: #333;
  --border-radius: 12px;
  --shadow: 0 2px 10px rgba(0,0,0,0.1);
}
```

### Layout Principal
```css
.chat-container {
  max-width: 800px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.input-area {
  position: sticky;
  bottom: 0;
  background: white;
}
```

### Messages
```css
.user-message {
  align-self: flex-end;
  background: var(--primary-color);
  color: white;
}

.ai-message {
  align-self: flex-start;
  background: var(--secondary-color);
  color: var(--text-color);
}
```

### Cartes Stations
```css
.station-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: var(--border-radius);
  padding: 16px;
  margin: 8px 0;
  box-shadow: var(--shadow);
  transition: transform 0.2s;
}

.station-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
```

### Badge "Meilleur Prix"
```css
.best-price {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}
```

---

## 📱 Responsive Design

```css
@media (max-width: 768px) {
  .chat-container {
    max-width: 100%;
  }
  
  .station-card {
    padding: 12px;
  }
  
  .suggestion-chip {
    font-size: 12px;
    padding: 6px 12px;
  }
}
```

---

## 🔄 Flow Complet d'Interaction

```
1. User tape "Prix du SP95"
   ↓
2. sendMessage() appelé
   ↓
3. Affichage message user (droite)
   ↓
4. Affichage typing indicator (...)
   ↓
5. sendToBackend(query)
   ├─ Lecture userLocation (GPS)
   ├─ POST http://127.0.0.1:8000/api/chat
   └─ Attente réponse
   ↓
6. Réception data JSON
   ↓
7. processResponse(data)
   ├─ Détection type (stations/parkings/text)
   └─ Formatage données
   ↓
8. Suppression typing indicator
   ↓
9. Affichage résultat
   ├─ Si stations → createStationCard × N
   ├─ Si parkings → createParkingCard × N
   └─ Si text → Message IA simple
   ↓
10. scrollToBottom()
```

---

## ⚡ Optimisations

### 1. Debouncing (non implémenté)
```javascript
let timeout;
input.addEventListener('input', () => {
  clearTimeout(timeout);
  timeout = setTimeout(() => {
    // Suggestions dynamiques
  }, 300);
});
```

### 2. Cache Local (non implémenté)
```javascript
localStorage.setItem('lastLocation', JSON.stringify(userLocation));
localStorage.setItem('chatHistory', JSON.stringify(messages));
```

### 3. Lazy Loading Images
```javascript
<img loading="lazy" src="..." />
```

---

## 🐛 Gestion des Erreurs

```javascript
async function sendToBackend(query) {
  try {
    const response = await fetch(...);
    
    if (!response.ok) {
      throw new Error(`Erreur ${response.status}`);
    }
    
    return await response.json();
    
  } catch (error) {
    console.error("❌ Erreur:", error);
    return {
      type: "text",
      text: "❌ Erreur de connexion au serveur"
    };
  }
}
```

---

## 🚀 Déploiement

### Serveur Local (Dev)
```bash
cd frontend
python -m http.server 3000
# Ou ouvrir directement index.html
```

### Production
- Héberger sur serveur web (Nginx, Apache)
- Configurer HTTPS
- Mettre à jour URL backend dans `script.js`
- Minifier JS/CSS
