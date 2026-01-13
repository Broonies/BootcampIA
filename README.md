Nouveau terminal pour Lancer le back :
cd backend
python -m uvicorn app.main:app --reload

Nouveau terminal pour lancer le front :
cd frontend
npm run dev

--------------------------------------------------------------------------------------------------------------------------------------------------------
# 🚗 Assistant Mobilité Rennes - IA Conversationnelle

> **Assistant IA intelligent pour les conducteurs de Rennes Métropole**  
> Propulsé par Qwen3:30B et données open-data en temps réel

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Fonctionnalités

### ⛽ Prix des Carburants
- Recherche des **stations les moins chères** par ville/code postal
- Support de tous les types : **Gazole, SP95, SP98, E10, E85, GPLc**
- Statistiques nationales en temps réel
- Cache intelligent (rafraîchissement quotidien)

### 🚦 Trafic en Temps Réel
- État du trafic sur **Rennes Métropole**
- Détection des axes perturbés
- Suggestions d'itinéraires alternatifs

### 🅿️ Stationnement
- Recommandations de parkings disponibles
- Données temps réel sur les places libres

### 🤖 Intelligence Artificielle
- Compréhension du langage naturel via **Qwen3:30B** (30 milliards de paramètres)
- Architecture **MCP-like** (Model Context Protocol)
- Contexte conversationnel persistant
