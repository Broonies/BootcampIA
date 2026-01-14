
--------------------------------------------------------------------------------------------------------------------------------------------------------
# 🚗 Assistant Mobilité Rennes - IA Conversationnelle

> **Assistant IA intelligent pour les conducteurs de Rennes Métropole**  
> Propulsé par Qwen3:30B et données open-data en temps réel

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?logo=javascript)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
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

### 📍 Calcul d'itinéraires GPS
- Estimation temps de trajet depuis votre position
- Support de 147 lieux de Rennes Métropole
- Recherche floue avec tolérance aux typos
- Intégration OSRM pour calcul de routes

### 🤖 Intelligence Artificielle
- Compréhension du langage naturel via **Qwen3:30B** (30 milliards de paramètres)
- Architecture **MCP-like** (Model Context Protocol)
- Contexte conversationnel persistant

---

## 📖 Utilisation

### Exemples de requêtes

**Prix carburant :**
```
"Prix du gazole à Rennes"
"Station essence la moins chère à 35000"
"Où trouver du SP95 pas cher ?"
```

**Trafic :**
```
"État du trafic à Rennes"
"Y a-t-il du trafic sur le périphérique ?"
```

**Itinéraires GPS :**
```
"Combien de temps pour aller à la gare depuis ma position ?"
"Temps pour aller à l'université Rennes 2 en partant de ma position"
"Aller à la place Saint Anne depuis ici"
```

**Parking :**
```
"Parkings disponibles à Rennes"
"Places libres centre-ville"
```

### 📍 Utiliser la position GPS

1. **Autorisez la géolocalisation** lorsque le navigateur le demande
2. Utilisez les phrases : `"ma position"`, `"depuis ma position"`, `"d'ici"`, `"où je suis"`
3. Le système reconnaît 147 lieux de Rennes (gare, universités, places, quartiers...)

**Lieux supportés :** gare, université rennes 1/2, place saint-anne, république, thabor, villejean, beaulieu, chu, etc.  
_Voir [GPS_INTEGRATION.md](GPS_INTEGRATION.md) pour la documentation technique complète_

