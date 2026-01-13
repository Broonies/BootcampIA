# backend/app/tools/traffic_scraper.py

import requests
from typing import Dict, List, Any, Optional
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime


class TrafficScraper:
    """
    Scraper pour les données de trafic en temps réel de Rennes Métropole
    Source: Opendatasoft API (données open-data officielles)
    """

    def __init__(self):
        self.base_url = "https://rennes-metropole.opendatasoft.com/api/records/1.0/search/"
        self.dataset = "etat-du-trafic-en-temps-reel"
        self._geocode_cache: Dict[str, Dict[str, str]] = {}

    def get_traffic_status(self, street_query: str | None = None) -> Dict[str, Any]:
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

            # Budget de géocodage pour éviter la lenteur (max 30 requêtes par appel)
            geocode_budget = 30

            # Helper geocode + enrichissement
            def _enrich(entry: Dict[str, Any], status_label: str, priority: str, can_geocode: bool) -> Dict[str, Any]:
                lat = entry.get("lat")
                lon = entry.get("lon")
                geocoded = {}
                if can_geocode and lat is not None and lon is not None:
                    geocoded = self._reverse_geocode(lat, lon) or {}

                display = geocoded.get("label") or entry.get("troncon")
                area = geocoded.get("area")
                return {
                    "street": display,
                    "raw_street": entry.get("troncon"),
                    "area": area,
                    "lat": lat,
                    "lon": lon,
                    "status": status_label,
                    "priority": priority
                }

            # Routes en congestion/incident (priorité haute)
            for entry in traffic_by_status["congestion"]:
                can_geo = geocode_budget > 0
                road_summary.append(_enrich(entry, "⚠️ Congestion", "haute", can_geo))
                if can_geo:
                    geocode_budget -= 1

            for entry in traffic_by_status["incident"]:
                can_geo = geocode_budget > 0
                road_summary.append(_enrich(entry, "🚨 Incident", "critique", can_geo))
                if can_geo:
                    geocode_budget -= 1

            # Routes denses (priorité moyenne) - limiter à 5
            for entry in traffic_by_status["denso"][:5]:
                can_geo = geocode_budget > 0
                road_summary.append(_enrich(entry, "📍 Dense", "moyen", can_geo))
                if can_geo:
                    geocode_budget -= 1

            # Si l'utilisateur a donné un nom de rue, tenter un appariement flou
            if street_query:
                road_summary = self._filter_best_match(road_summary, street_query)

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

    def _reverse_geocode(self, lat: float, lon: float) -> Dict[str, str]:
        """Reverse geocode via Nominatim (OSM) with simple cache, Rennes only"""
        key = f"{lat:.5f},{lon:.5f}"
        if key in self._geocode_cache:
            return self._geocode_cache[key]

        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "jsonv2",
                    "zoom": 18,
                    "addressdetails": 1
                },
                headers={"User-Agent": "FuelBot-Rennes/1.0"},
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            address = data.get("address", {})

            road = address.get("road") or address.get("pedestrian") or address.get("residential")
            area = address.get("neighbourhood") or address.get("suburb") or address.get("city_district")
            city = address.get("city") or address.get("town")
            postcode = address.get("postcode")

            # Ne garder que Rennes / CP 35***
            if postcode and not str(postcode).startswith("35"):
                result = {"label": road or data.get("display_name", "Rennes"), "area": area}
            else:
                result = {
                    "label": ", ".join([p for p in [road, area] if p]) or road or data.get("display_name", "Rennes"),
                    "area": area,
                    "city": city,
                    "postcode": postcode
                }

            self._geocode_cache[key] = result
            return result
        except Exception:
            return {}

    @staticmethod
    def _normalize(text: str) -> str:
        """Minuscule + suppression des accents et espaces multiples"""
        if not text:
            return ""
        text = text.lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        return " ".join(text.split())

    def _fuzzy_score(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def _filter_best_match(self, roads: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Renvoie les tronçons les plus proches du nom demandé"""
        norm_q = self._normalize(query)
        if not norm_q:
            return roads

        scored: List[tuple[float, Dict[str, Any]]] = []
        for r in roads:
            candidates = [r.get("street"), r.get("raw_street"), r.get("area")]
            best = 0.0
            for c in candidates:
                if not c:
                    continue
                score = self._fuzzy_score(norm_q, self._normalize(str(c)))
                best = max(best, score)
            scored.append((best, r))

        # Garder ceux au-dessus d'un seuil, sinon renvoyer le meilleur seul
        threshold = 0.55
        scored.sort(key=lambda x: x[0], reverse=True)
        top_score = scored[0][0] if scored else 0
        filtered = [r for s, r in scored if s >= max(threshold, top_score - 0.05)]

        return filtered if filtered else roads
