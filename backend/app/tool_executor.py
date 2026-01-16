"""Exécution d'outils pour le simulateur MCP."""
from typing import Dict, Any, Optional, Tuple

from .tools.fuel_scraper import FuelPriceScraper, calculate_distance
from .tools.traffic_scraper import TrafficScraper
from .tools.parking_scraper import ParkingScraper
from .tools.drive_time_estimator import DriveTimeEstimator
from .rennes_locations import find_location_fuzzy, get_suggestions


class ToolExecutor:
    """Exécute les outils MCP avec les paramètres donnés."""
    
    def __init__(self):
        self.fuel_scraper = FuelPriceScraper(restrict_to_rennes=True)
        self.traffic_scraper = TrafficScraper()
        self.parking_scraper = ParkingScraper()
        self.drive_time_estimator = DriveTimeEstimator()
        
        # Mapping des outils disponibles
        self.tools = {
            "search_fuel_prices": self._search_fuel_prices,
            "get_cheapest_station": self._get_cheapest_station,
            "compare_fuel_prices": self._compare_fuel_prices,
            "get_fuel_stats": self._get_fuel_stats,
            "get_traffic_status": self._get_traffic_status,
            "get_parking_status": self._get_parking_status,
            "estimate_drive_time": self._estimate_drive_time,
            "scrape_website": self._detect_scraping,
        }
    
    def execute(self, tool_name: str, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Exécute un outil MCP avec les paramètres donnés.
        
        Args:
            tool_name: Nom de l'outil à exécuter
            params: Paramètres extraits du message
            user_location: Tuple (latitude, longitude) de l'utilisateur (optionnel)
            
        Returns:
            Résultat de l'exécution de l'outil
        """
        if tool_name in self.tools:
            return self.tools[tool_name](params, user_location)
        return {"error": f"Outil {tool_name} inconnu"}
    
    def _search_fuel_prices(self, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Recherche les prix de carburant."""
        ville = params.get('ville')
        code_postal = params.get('code_postal')
        fuel_type = params.get('fuel_type', 'Gazole')
        
        try:
            if code_postal:
                results = self.fuel_scraper.search_by_postal_code(code_postal, fuel_type)
            elif ville:
                results = self.fuel_scraper.search_by_city(ville, fuel_type)
            else:
                return {"error": "Ville ou code postal requis"}
            
            # 📍 Ajouter les distances si position GPS disponible
            if user_location:
                station_data = self.fuel_scraper.fetch_daily_prices()
                for result in results:
                    # Chercher les coordonnées de la station
                    for station in station_data["stations"]:
                        if (station["adresse"] == result["adresse"] and 
                            station["cp"] == result["cp"]):
                            if "latitude" in station and "longitude" in station:
                                distance = calculate_distance(
                                    user_location[0], user_location[1],
                                    station["latitude"], station["longitude"]
                                )
                                result["distance_km"] = distance
                            break
            
            return {
                "success": True,
                "fuel_type": fuel_type,
                "location": ville or code_postal,
                "results": results[:10],
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_cheapest_station(self, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Trouve les stations les moins chères."""
        ville = params.get('ville')
        code_postal = params.get('code_postal')
        fuel_type = params.get('fuel_type', 'Gazole')
        limit = params.get('limit', 5)
        
        try:
            if code_postal:
                results = self.fuel_scraper.search_by_postal_code(code_postal, fuel_type)
            elif ville:
                results = self.fuel_scraper.get_cheapest_in_city(ville, fuel_type, limit)
            else:
                return {"error": "Ville ou code postal requis"}
            
            # 📍 Ajouter les distances si position GPS disponible
            if user_location:
                station_data = self.fuel_scraper.fetch_daily_prices()
                for result in results:
                    # Chercher les coordonnées de la station
                    for station in station_data["stations"]:
                        if (station["adresse"] == result["adresse"] and 
                            station["cp"] == result["cp"]):
                            if "latitude" in station and "longitude" in station:
                                distance = calculate_distance(
                                    user_location[0], user_location[1],
                                    station["latitude"], station["longitude"]
                                )
                                result["distance_km"] = distance
                            break
            
            return {
                "success": True,
                "fuel_type": fuel_type,
                "location": ville or code_postal,
                "cheapest_stations": results[:limit]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _compare_fuel_prices(self, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Compare les prix entre plusieurs villes."""
        return {"info": "Comparaison non implémentée"}
    
    def _get_fuel_stats(self, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Retourne les statistiques globales."""
        try:
            stats = self.fuel_scraper.get_stats()
            return {
                "success": True,
                "stats": stats
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _estimate_drive_time(self, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Estime le temps de trajet en tenant compte du trafic."""
        try:
            origin_name = params.get('origin_name', 'Rennes Centre')
            destination_name = params.get('destination_name', 'Rennes')
            
            print(f"[DRIVE TIME DEBUG] origin_name='{origin_name}', user_location={user_location}")
            
            # Déterminer les coordonnées d'origine
            if user_location and origin_name.lower() in ['ma position', 'position actuelle', 'où je suis', 'ici']:
                origin_coords = user_location
                print(f"[DRIVE TIME] ✓ Utilisant position GPS de l'utilisateur: {origin_coords}")
            else:
                print(f"[DRIVE TIME] ✗ user_location={user_location}, origin_name.lower()='{origin_name.lower()}'")
                origin_coords = find_location_fuzzy(origin_name)
                if not origin_coords:
                    suggestions = get_suggestions(origin_name, limit=3)
                    suggestion_text = f" Vouliez-vous dire: {', '.join(suggestions[:3])} ?" if suggestions else ""
                    return {
                        "success": False,
                        "error": f"Lieu de départ '{origin_name}' inconnu.{suggestion_text}"
                    }
            
            # Déterminer les coordonnées de destination
            dest_coords = find_location_fuzzy(destination_name)
            if not dest_coords:
                suggestions = get_suggestions(destination_name, limit=3)
                suggestion_text = f" Vouliez-vous dire: {', '.join(suggestions[:3])} ?" if suggestions else ""
                return {
                    "success": False,
                    "error": f"Lieu d'arrivée '{destination_name}' inconnu.{suggestion_text}"
                }
            
            result = self.drive_time_estimator.estimate_drive_time(
                origin_coords, dest_coords
            )
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_traffic_status(self, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Retourne l'état du trafic pour Rennes Métropole."""
        return self.traffic_scraper.get_traffic_status(params.get("street_query"))
    
    def _get_parking_status(self, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Retourne la disponibilité des parkings à Rennes."""
        return self.parking_scraper.get_parking_status(user_location)
    
    def _detect_scraping(self, params: Dict[str, Any], user_location: Optional[Tuple[float, float]] = None) -> bool:
        """Détecte si scraping nécessaire."""
        return True
