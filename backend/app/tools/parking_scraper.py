# backend/app/tools/parking_scraper.py

import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .fuel_scraper import calculate_distance


class ParkingScraper:
    """
    Scraper pour les données de parkings en temps réel de Rennes Métropole
    Source: API Opendatasoft (données open-data officielles)
    """

    def __init__(self):
        self.base_url = "https://data.rennesmetropole.fr/api/records/1.0/search/"
        self.dataset = "export-api-parking-citedia"

    def get_parking_status(self, user_location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Récupère les disponibilités des parkings de Rennes
        
        Returns:
            {
                "success": bool,
                "parkings": [
                    {
                        "name": str,
                        "available": int,
                        "total": int,
                        "status": str,
                        "location": str,
                        "distance_km": float | None
                    }
                ],
                "updated": str (HH:MM),
                "total_parkings": int
            }
        """
        try:
            response = requests.get(
                self.base_url,
                params={
                    "dataset": self.dataset,
                    "rows": 100
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            records = data.get("records", [])
            parkings = []

            for rec in records:
                fields = rec.get("fields", {})
                
                name = fields.get("key", "Parking inconnu")
                available = int(fields.get("free", 0))
                total = int(fields.get("max", 0))
                status_api = fields.get("status", "")
                
                # Récupérer les tarifs
                pricing = {}
                tarif_fields = {
                    "15min": fields.get("tarif_15"),
                    "30min": fields.get("tarif_30"),
                    "1h": fields.get("tarif_1h"),
                    "1h30": fields.get("tarif_1h30"),
                    "2h": fields.get("tarif_2h"),
                    "3h": fields.get("tarif_3h"),
                    "4h": fields.get("tarif_4h")
                }
                
                for duree, prix in tarif_fields.items():
                    if prix is not None:
                        try:
                            prix_float = float(prix)
                            if prix_float > 0:
                                pricing[duree] = f"{prix_float}€"
                        except (ValueError, TypeError):
                            continue
                
                # Calculer le statut en fonction des places disponibles
                if status_api == "FERME":
                    status = "🔴 Fermé"
                elif available == 0:
                    status = "🔴 Complet"
                elif available < 10:
                    status = "🟠 Peu de places"
                elif available < 50:
                    status = "🟡 Places disponibles"
                else:
                    status = "🟢 Nombreuses places"
                
                # Géolocalisation si disponible
                geo = fields.get("geo", [])
                location = f"{geo[0]:.5f}, {geo[1]:.5f}" if len(geo) == 2 else ""
                distance_km = None
                if user_location and len(geo) == 2:
                    distance_km = calculate_distance(
                        user_location[0], user_location[1], geo[0], geo[1]
                    )
                
                parking_data = {
                    "name": name,
                    "available": available,
                    "total": total,
                    "status": status,
                    "location": location,
                    "occupancy_rate": round((total - available) / total * 100, 1) if total > 0 else 0,
                    "distance_km": distance_km,
                }
                
                # Ajouter les tarifs seulement s'il y en a
                if pricing:
                    parking_data["pricing"] = pricing
                
                parkings.append(parking_data)

            # Trier par distance si GPS fourni, sinon par places disponibles
            if user_location:
                parkings.sort(key=lambda x: (x["distance_km"] is None, x.get("distance_km", 1e9)))
            else:
                parkings.sort(key=lambda x: x["available"], reverse=True)

            return {
                "success": True,
                "parkings": parkings,
                "updated": self._get_current_time(),
                "total_parkings": len(parkings)
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout: données parkings indisponibles"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Erreur de connexion aux données parkings"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur récupération parkings: {str(e)}"
            }

    @staticmethod
    def _get_current_time() -> str:
        """Retourne l'heure actuelle formatée HH:MM"""
        return datetime.now().strftime("%H:%M")
