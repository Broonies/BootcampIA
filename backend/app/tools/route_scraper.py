"""
Scraper de routes utilisant OSRM (Open Source Routing Machine)
Fournit le routage et l'estimation du temps de trajet
"""

import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class RouteScraper:
    """
    Récupère les itinéraires via OSRM
    Utilise l'API publique OSRM pour calculer les routes
    """

    def __init__(self):
        # API OSRM publique (https://router.project-osm.org/)
        self.osrm_url = "https://router.project-osrm.org/route/v1/driving"

    @staticmethod
    def _decode_polyline(polyline: str) -> List[Tuple[float, float]]:
        """
        Décode une polyline encodée (format polyline6)
        Retourne une liste de coordonnées [lon, lat]
        """
        coords = []
        index, lat, lng = 0, 0, 0
        
        while index < len(polyline):
            result = 0
            shift = 0
            
            while True:
                byte = ord(polyline[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break
            
            dlat = ~result >> 1 if result & 1 else result >> 1
            lat += dlat
            
            result = 0
            shift = 0
            
            while True:
                byte = ord(polyline[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break
            
            dlng = ~result >> 1 if result & 1 else result >> 1
            lng += dlng
            
            coords.append([lng / 1e6, lat / 1e6])
        
        return coords

    def get_route(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        Récupère un itinéraire entre deux points (lat, lon)
        
        Returns:
            {
                "success": bool,
                "distance_km": float,
                "duration_seconds": int,
                "duration_minutes": float,
                "coordinates": [[lon, lat], ...],
                "error": str (si erreur)
            }
        """
        try:
            # OSRM utilise (lon, lat) contrairement à (lat, lon)
            coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"

            response = requests.get(
                f"{self.osrm_url}/{coords}",
                params={
                    "overview": "full",  # Retourner les coordonnées complètes
                    "steps": "false",
                    "annotations": "duration,distance"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok":
                return {
                    "success": False,
                    "error": f"OSRM erreur: {data.get('code', 'Unknown')}"
                }

            route = data.get("routes", [{}])[0]
            distance_m = route.get("distance", 0)
            duration_s = int(route.get("duration", 0))
            
            # La géométrie est une polyline encodée (string), pas un dict
            geometry = route.get("geometry", "")
            if isinstance(geometry, str):
                coordinates = self._decode_polyline(geometry)
            else:
                # Repli si le format est différent
                coordinates = geometry.get("coordinates", [])

            return {
                "success": True,
                "distance_km": round(distance_m / 1000, 2),
                "duration_seconds": duration_s,
                "duration_minutes": round(duration_s / 60, 1),
                "coordinates": coordinates,  # [[lon, lat], ...]
                "origin": origin,
                "destination": destination
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout OSRM: serveur trop lent"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Erreur connexion OSRM"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur OSRM: {str(e)}"
            }

    @staticmethod
    def _get_current_time() -> str:
        """Retourne l'heure actuelle formatée HH:MM"""
        return datetime.now().strftime("%H:%M")
