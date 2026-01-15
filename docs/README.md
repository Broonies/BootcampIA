# 📚 Documentation Technique - FuelBot

Assistant IA de mobilité pour Rennes Métropole.

---

## 📖 Table des Matières

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Vue d'ensemble de l'architecture système
   - Structure du projet
   - Flux de données
   - Composants clés
   - Stack technologique

2. **[API.md](./API.md)** - Documentation API REST
   - Endpoints disponibles
   - Formats requête/réponse
   - Exemples d'utilisation
   - Codes d'erreur

3. **[MCP_TOOLS.md](./MCP_TOOLS.md)** - Outils MCP et détection
   - Système de détection d'outils
   - Extraction de paramètres
   - Scrapers et sources de données
   - Calcul GPS

4. **[FRONTEND.md](./FRONTEND.md)** - Documentation Frontend
   - Structure HTML/CSS/JS
   - Composants UI
   - Géolocalisation
   - Flow d'interaction

5. **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Guide de déploiement
   - Installation et configuration
   - Déploiement local/cloud
   - Sécurité production
   - Monitoring

---

## 🚀 Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
python -m http.server 3000
# Ou ouvrir index.html directement
```

---

## 🔗 Liens Utiles

- **API Rennes Métropole** : https://data.rennesmetropole.fr
- **Données Carburant** : https://donnees.roulez-eco.fr
- **FastAPI Docs** : https://fastapi.tiangolo.com
- **Ollama** : https://ollama.ai

---

## 📊 Schéma Simplifié

```
┌──────────┐
│ Frontend │ ──→ POST /api/chat (+ GPS)
└────┬─────┘
     ↓
┌────────────────────┐
│ Backend FastAPI    │
│ ┌────────────────┐ │
│ │ MCP Simulator  │ │ ──→ 1. Détection outil
│ │ • Detector     │ │     2. Extraction params
│ │ • Extractor    │ │     3. Exécution + GPS
│ │ • Executor     │ │
│ └────────────────┘ │
│ ┌────────────────┐ │
│ │ LLM (Ollama)   │ │ ──→ Génération réponse
│ └────────────────┘ │
└────┬───────────────┘
     ↓
┌──────────────────┐
│ Outils MCP       │
│ • Carburant      │ ──→ API Open Data
│ • Parking        │ ──→ API Rennes
│ • Trafic         │ ──→ API Rennes
│ • Trajet         │ ──→ Calcul local
└──────────────────┘
```

---

## 🛠️ Technologies

| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI (Python 3.13) |
| Frontend | HTML5, Vanilla JS, CSS3 |
| LLM | Ollama (qwen3:30b) |
| Data | XML/JSON Scraping + APIs REST |
| GPS | Haversine formula |
| Cache | JSON local (24h) |

---

## 👥 Contribution

Pour contribuer :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit changements (`git commit -m 'Ajout fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

---

## 📝 Changelog

### v1.0 (2026-01-15)
- ✅ Système MCP fonctionnel
- ✅ Calcul distances GPS
- ✅ Frontend responsive
- ✅ Cache 24h carburant
- ✅ 4 outils : carburant, parking, trafic, trajet

### À venir (v1.1)
- 🔄 Détection par LLM
- 🔄 Multi-tool dans une requête
- 🔄 Historique conversation
- 🔄 Favoris utilisateur

---

## 📞 Support

Pour questions ou bugs :
- 📧 Email : support@fuelbot.fr
- 🐛 Issues : GitHub Issues
- 💬 Discord : [Lien serveur]

---

**Dernière mise à jour** : 15 janvier 2026
