"""Détection d'outils pour le simulateur MCP."""
import re
import unicodedata
from typing import Optional


class ToolDetector:
    """Détecte quel outil utiliser en fonction du message utilisateur."""
    
    @staticmethod
    def _remove_accents(text: str) -> str:
        """Supprime les accents d'une chaîne"""
        nfd = unicodedata.normalize('NFD', text)
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    def __init__(self):
        # Mots-clés pour chaque catégorie d'outil
        self.fuel_keywords = [
            'gazole', 'essence', 'carburant', 'sp95', 'sp98', 'e10', 'e85',
            'seation', 'prix', 'moins cher', 'pas cher', 'economique',
        ]
        
        self.nearest_fuel_keywords = [
            'station essence', 'station', 'carburant', 'essence',
            'proche', 'proxime', 'plus proche', 'pres', 'près',
            'a proximite', 'à proximité', 'le plus proche'
        ]
        
        self.traffic_keywords = [
            'traffic', 'bouchons', 'congestion', 'embouteillage',
            'circulation', 'route', 'routes', 'autoroute', 'voie', 'rue', 'boulevard',
            'péage', 'temps de trajet', 'ralentissement', 'accident',
            'tfic', 'trafic', 'bouchon', 'ralenti',
        ]
        
        self.drive_keywords = [
            'temps', 'trajet', 'combien de temps', 'temps de route',
            'duree', 'aller a', 'me rendre', 'aller de', 'depuis', 'vers',
            'comment', 'long', 'dure', 'quelle heure', 'arriver', 'parcourir',
            'distance', 'km'
        ]
        
        self.parking_keywords = [
            'parking', 'parkings', 'stationner', 'stationnement',
            'place', 'places', 'garer', 'garage', 'park'
        ]
        
        self.nearest_parking_keywords = [
            'parking', 'parkings', 'stationnement',
            'proche', 'proxime', 'plus proche', 'pres', 'près',
            'a proximite', 'à proximité', 'le plus proche'
        ]
    
    def detect(self, user_message: str) -> Optional[str]:
        """
        Détecte quel outil MCP utiliser basé sur le message utilisateur.
        
        Args:
            user_message: Message de l'utilisateur
            
        Returns:
            Nom de l'outil à utiliser ou None
        """
        message_lower = user_message.lower()
        message_no_accents = self._remove_accents(message_lower)
        
        # LOGIQUE POUR LES REQUETES STATION ESSENCE PROCHE
        if all(any(keyword in message_no_accents for keyword in keywords) 
               for keywords in [self.fuel_keywords, self.nearest_fuel_keywords]):
            return "find_nearest_fuel_station"
        
        # LOGIQUE POUR LES REQUETES CARBURANT
        if any(keyword in message_no_accents for keyword in self.fuel_keywords):
            # Déterminer le type de requête carburant
            if any(word in message_no_accents for word in ['moins cher', 'cheapest', 'economique', 'pas cher']):
                return "get_cheapest_station"
            elif any(word in message_no_accents for word in ['compare', 'comparaison', 'difference']):
                return "compare_fuel_prices"
            elif any(word in message_no_accents for word in ['statistique', 'moyenne', 'stats']):
                return "get_fuel_stats"
            else:
                return "search_fuel_prices"
        
        # LOGIQUE POUR LES REQUETES TRAJET/TEMPS DE ROUTE
        if any(word in message_no_accents for word in self.drive_keywords):
            # Vérifier qu'on a au moins 2 localisations ou une position personnelle
            if any(phrase in message_no_accents for phrase in ['a', 'vers', 'de', 'au', 'ma position', 'mon emplacement']):
                return "estimate_drive_time"
        
        # Fallback: pattern "de X a Y" sans keywords spécifiques
        if re.search(r'\bde\s+.+?\s+(?:a|à)\s+', message_no_accents):
            return "estimate_drive_time"
        
        # LOGIQUE POUR LES REQUETES TRAFIC
        if any(word in message_no_accents for word in self.traffic_keywords):
            return "get_traffic_status"
        
        # LOGIQUE POUR LES REQUETES PARKING
        if any(word in message_no_accents for word in self.parking_keywords):
            return "get_parking_status"
        
        return None
