# Guide de Déploiement - FuelBot

## 🛠️ Prérequis

### Système
- Python 3.13+
- Node.js (optionnel, pour frontend)
- Git

### Services Externes
- **Ollama** : Serveur LLM local
  - Modèle : `qwen3:30b`
  - URL : `http://localhost:11434`

---

## 📦 Installation

### 1. Cloner le Projet
```bash
git clone <repository-url>
cd BootcampIA
```

### 2. Backend Setup

#### Environnement Virtuel (recommandé)
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### Installation Dépendances
```bash
pip install -r requirements.txt
```

**Contenu `requirements.txt`** :
```txt
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
requests==2.31.0
python-dotenv==1.0.0
beautifulsoup4==4.12.3
lxml==5.1.0
```

#### Configuration
Créer `.env` dans `/backend` :
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:30b
RENNES_LAT=48.1173
RENNES_LON=-1.6778
```

### 3. Frontend Setup
```bash
cd frontend
# Aucune installation nécessaire (Vanilla JS)
```

---

## 🚀 Lancement

### Backend

#### Développement
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Ou avec le script** :
```bash
cd BootcampIA
python run_backend.py
```

#### Production
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Avec Gunicorn** (Linux) :
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Frontend

#### Développement
```bash
cd frontend
python -m http.server 3000
```

**Ou ouvrir directement** :
```bash
# Windows
start index.html

# Mac
open index.html

# Linux
xdg-open index.html
```

#### Production
Héberger sur Nginx, Apache, ou service cloud (Vercel, Netlify).

---

## 🐳 Docker (Optionnel)

### Dockerfile Backend
```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    volumes:
      - ./backend/cache:/app/cache

  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
```

### Lancement
```bash
docker-compose up -d
```

---

## ☁️ Déploiement Cloud

### Backend → Railway / Render

#### 1. **Render.com**
```yaml
# render.yaml
services:
  - type: web
    name: fuelbot-api
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OLLAMA_BASE_URL
        value: http://your-ollama-server:11434
```

#### 2. **Railway**
```bash
railway login
railway init
railway up
```

### Frontend → Vercel / Netlify

#### 1. **Vercel**
```bash
cd frontend
vercel --prod
```

#### 2. **Netlify**
```bash
cd frontend
netlify deploy --prod --dir=.
```

**Configuration** : Mettre à jour URL backend dans `script.js` :
```javascript
const BACKEND_URL = "https://fuelbot-api.render.com";
```

---

## 🔒 Sécurité Production

### 1. CORS Restrictif
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://votre-domaine.com"],  # ← Restreindre
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

### 2. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat(request: ChatRequest):
    ...
```

### 3. Variables d'Environnement
Ne **jamais** commit `.env` :
```bash
echo ".env" >> .gitignore
```

### 4. HTTPS
- Utiliser Let's Encrypt (Certbot)
- Ou certificat cloud provider (Cloudflare, AWS)

---

## 📊 Monitoring

### 1. Logs
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Health Check
```bash
curl http://localhost:8000/api/health
```

### 3. Prometheus (Optionnel)
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

---

## 🧪 Tests Pré-Déploiement

### Backend
```bash
pytest tests/
```

### API Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Prix gazole", "latitude": 48.1104, "longitude": -1.6769}'
```

### Frontend
- Ouvrir navigateur → DevTools → Console
- Vérifier géolocalisation
- Tester toutes les suggestions

---

## 🐛 Troubleshooting

### Backend ne démarre pas
```bash
# Vérifier port disponible
netstat -ano | findstr :8000

# Tuer processus si occupé
taskkill /PID <PID> /F  # Windows
kill -9 <PID>            # Linux/Mac
```

### CORS Error
```
Access-Control-Allow-Origin...
```
→ Vérifier `allow_origins` dans `main.py`

### LLM Error
```
Connection refused to Ollama
```
→ Vérifier Ollama tourne : `curl http://localhost:11434`

### GPS non disponible
→ Fallback automatique à Rennes centre (48.1104, -1.6769)

---

## 📈 Optimisations Production

### 1. Cache Redis
```python
import redis

cache = redis.Redis(host='localhost', port=6379)

def get_fuel_prices():
    cached = cache.get('fuel_prices')
    if cached:
        return json.loads(cached)
    
    data = scraper.fetch()
    cache.setex('fuel_prices', 3600, json.dumps(data))
    return data
```

### 2. CDN pour Frontend
- Héberger assets statiques sur Cloudflare/AWS S3
- Activer compression Gzip/Brotli

### 3. Database
- Migrer cache JSON → PostgreSQL/MongoDB
- Indexer sur `cp`, `ville`, `fuel_type`

---

## 🔄 CI/CD (Optionnel)

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy Backend
        run: |
          ssh user@server "cd /app && git pull && systemctl restart fuelbot"
      
      - name: Deploy Frontend
        run: vercel --prod
```

---

## 📚 Checklist Déploiement

- [ ] Variables d'environnement configurées
- [ ] CORS restreint au domaine production
- [ ] HTTPS activé
- [ ] Rate limiting configuré
- [ ] Logs activés
- [ ] Health check opérationnel
- [ ] Tests passent
- [ ] Cache optimisé
- [ ] Monitoring configuré
- [ ] Backup données planifié
