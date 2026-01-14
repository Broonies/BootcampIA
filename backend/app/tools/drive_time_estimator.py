"""
Estimateur de temps de trajet avec intégration du trafic
Estime le temps de trajet en tenant compte des conditions de trafic
"""

from typing import Dict, List, Any, Tuple
from shapely.geometry import LineString, Point
from .route_scraper import RouteScraper
from .traffic_scraper import TrafficScraper


class DriveTimeEstimator:
    """
    Estime le temps de trajet en intégrant les données de trafic
    """

    def __init__(self):
        self.route_scraper = RouteScraper()
        self.traffic_scraper = TrafficScraper()

        # Multiplicateurs de temps selon l'état du trafic
        self.traffic_multipliers = {
            "fluide": 1.0,
            "denso": 1.5,
            "congestion": 2.0,
            "critique": 3.0,
            "incident": 3.0
        }

        # Buffer pour considérer qu'une perturbation affecte la route (en km)
        self.impact_buffer_km = 0.5

    def estimate_drive_time(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        Estime le temps de trajet entre deux points en tenant compte du trafic
        
        Args:
            origin: (lat, lon)
            destination: (lat, lon)
        
        Returns:
            {
                "success": bool,
                "origin": (lat, lon),
                "destination": (lat, lon),
                "distance_km": float,
                "duration_base_minutes": float,
                "traffic_impact_minutes": float,
                "duration_estimated_minutes": float,
                "affected_roads": [{"street", "status", "impact_min"}],
                "warning": str (si problèmes majeurs)
            }
        """
        try:
            # 1) Récupérer l'itinéraire
            route = self.route_scraper.get_route(origin, destination)
            if not route.get("success"):
                return {
                    "success": False,
                    "error": route.get("error", "Erreur OSRM")
                }

            distance_km = route["distance_km"]
            duration_base_sec = route["duration_seconds"]
            duration_base_min = route["duration_minutes"]
            coordinates = route["coordinates"]  # [[lon, lat], ...]

            # 2) Pour maintenant, retourner estimation sans trafic (traffic_scraper est trop lent)
            # À FAIRE: Optimiser le traffic scraper avec cache et requêtes parallèles
            return {
                "success": True,
                "origin": origin,
                "destination": destination,
                "distance_km": distance_km,
                "duration_base_minutes": duration_base_min,
                "traffic_impact_minutes": 0,
                "duration_estimated_minutes": duration_base_min,
                "affected_roads": [],
                "warning": "Trafic non disponible (service en optimisation)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur estimation: {str(e)}"
            }
