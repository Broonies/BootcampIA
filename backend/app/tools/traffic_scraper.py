# backend/app/tools/traffic_scraper.py

import requests
from typing import Dict, List, Any, Optional
from datetime import datetime


class TrafficScraper:
    """
    Scraper pour les données de trafic en temps réel de Rennes Métropole
    Source: Opendatasoft API (données open-data officielles)
    """

    def __init__(self):
        self.base_url = "https://rennes-metropole.opendatasoft.com/api/records/1.0/search/"
        self.dataset = "etat-du-trafic-en-temps-reel"

    def get_traffic_status(self) -> Dict[str, Any]:
        """
        Récupère et formate les données de trafic pour Rennes Métropole
        
        Returns:
            {
                "success": bool,
                "roads": [
                    {
                        "street": str,
                        "status": str (emoji + texte),
                        "priority": "critique" | "haute" | "moyen" | None
                    }
                ],
                "summary": str,
                "updated": str (HH:MM),
                "total_monitored": int
            }
        """
        try:
            # 1) Récupérer les données
            response = requests.get(
                self.base_url,
                params={
                    "dataset": self.dataset,
                    "rows": 5000
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # 2) Parser et classifier par statut
            records = data.get("records", [])
            
            traffic_by_status = {
                "fluide": [],
                "denso": [],
                "congestion": [],
                "incident": []
            }

            for rec in records:
                fields = rec.get("fields", {})

                # Les libellés de tronçon peuvent se trouver dans plusieurs champs selon l'API
                troncon = (
                    fields.get("predefinedlocationreference")
                    or fields.get("predefinedlocationrerefence")  # faute courante dans l'API
                    or fields.get("linearreferencename")
                    or fields.get("roadname")
                    or fields.get("segmentname")
                    or "Voie non identifiée"
                )

                # Coordonnées si disponibles
                location = fields.get("geo_point_2d") or fields.get("geo_shape", {}).get("coordinates")
                lat = None
                lon = None
                if isinstance(location, list) and len(location) == 2:
                    lat, lon = location[0], location[1]

                status_raw = str(fields.get("trafficstatus", "")).lower()

                # Normaliser le statut
                if "fluide" in status_raw or "free" in status_raw:
                    status = "fluide"
                elif "dense" in status_raw or "dens" in status_raw:
                    status = "denso"
                elif "congestion" in status_raw or "congested" in status_raw:
                    status = "congestion"
                else:
                    status = "incident"

                traffic_by_status[status].append({
                    "troncon": troncon,
                    "lat": lat,
                    "lon": lon
                })

            # 3) Structurer pour le LLM - synthèse par statut
            road_summary = []

            # Routes en congestion/incident (priorité haute)
            for entry in traffic_by_status["congestion"]:
                road_summary.append({
                    "street": entry.get("troncon"),
                    "lat": entry.get("lat"),
                    "lon": entry.get("lon"),
                    "status": "⚠️ Congestion",
                    "priority": "haute"
                })

            for entry in traffic_by_status["incident"]:
                road_summary.append({
                    "street": entry.get("troncon"),
                    "lat": entry.get("lat"),
                    "lon": entry.get("lon"),
                    "status": "🚨 Incident",
                    "priority": "critique"
                })

            # Routes denses (priorité moyenne) - limiter à 5
            for entry in traffic_by_status["denso"][:5]:
                road_summary.append({
                    "street": entry.get("troncon"),
                    "lat": entry.get("lat"),
                    "lon": entry.get("lon"),
                    "status": "📍 Dense",
                    "priority": "moyen"
                })

            # Générer résumé
            summary = self._generate_summary(traffic_by_status)

            return {
                "success": True,
                "roads": road_summary,
                "summary": summary,
                "updated": self._get_current_time(),
                "total_monitored": len(records)
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout: données de trafic indisponibles (serveur trop lent)"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Erreur de connexion: impossible d'accéder aux données de trafic"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur lors de la récupération du trafic: {str(e)}"
            }

    def _generate_summary(self, traffic_by_status: Dict[str, list]) -> str:
        """Génère un résumé textuel du trafic"""
        incidents = len(traffic_by_status["incident"])
        congestions = len(traffic_by_status["congestion"])
        dense = len(traffic_by_status["denso"])

        if incidents == 0 and congestions == 0 and dense == 0:
            return "Trafic fluide sur Rennes Métropole"

        parts = []
        if incidents > 0:
            parts.append(f"{incidents} incident(s)")
        if congestions > 0:
            parts.append(f"{congestions} congestion(s)")
        if dense > 0:
            parts.append(f"{dense} zone(s) dense(s)")

        return "Trafic: " + ", ".join(parts)

    @staticmethod
    def _get_current_time() -> str:
        """Retourne l'heure actuelle formatée HH:MM"""
        return datetime.now().strftime("%H:%M")
