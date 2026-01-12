# backend/app/mcp_sim.py
import re
from typing import Optional, Dict, Any
from backend.app.tools.fuel_scraper import FuelPriceScraper

class MCPSimulator:
    """
    Simule un serveur MCP avec outils de scraping et prix carburants
    """
    
    def __init__(self):
        self.fuel_scraper = FuelPriceScraper()
        
        # Mapping des outils disponibles
        self.tools = {
            "search_fuel_prices": self._search_fuel_prices,
            "get_cheapest_station": self._get_cheapest_station,
            "compare_fuel_prices": self._compare_fuel_prices,
            "get_fuel_stats": self._get_fuel_stats,
            "scrape_website": self._detect_scraping,
        }
    
    def detect_tool_needed(self, user_message: str) -> Optional[str]:
        """
        Détecte quel outil MCP utiliser basé sur le message utilisateur
        """
        message_lower = user_message.lower()
        
        # Détection prix carburant
        fuel_keywords = [
            'gazole', 'essence', 'carburant', 'sp95', 'sp98', 'e10', 'e85',
            'station', 'prix', 'moins cher', 'pas cher', 'économique'
        ]
        
        if any(keyword in message_lower for keyword in fuel_keywords):
            # Déterminer le type de requête carburant
            if any(word in message_lower for word in ['moins cher', 'cheapest', 'économique', 'pas cher']):
                return "get_cheapest_station"
            elif any(word in message_lower for word in ['compare', 'comparaison', 'différence']):
                return "compare_fuel_prices"
            elif any(word in message_lower for word in ['statistique', 'moyenne', 'stats']):
                return "get_fuel_stats"
            else:
                return "search_fuel_prices"
        
        # Détection scraping classique
        if re.search(r'https?://\S+', user_message):
            return "scrape_website"
        
        if any(keyword in message_lower for keyword in ['scrape', 'récupère', 'extrait']):
            return "scrape_website"
        
        return None
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un outil MCP avec les paramètres donnés
        """
        if tool_name in self.tools:
            return self.tools[tool_name](params)
        return {"error": f"Outil {tool_name} inconnu"}
    
    def _extract_params_from_message(self, message: str, tool_name: str) -> Dict[str, Any]:
        """
        Extrait automatiquement les paramètres du message utilisateur
        """
        message_lower = message.lower()
        params = {}
        
        # Extraction du type de carburant
        fuel_types = {
            'gazole': 'Gazole',
            'diesel': 'Gazole',
            'sp95': 'SP95',
            'sp98': 'SP98',
            'e10': 'E10',
            'e85': 'E85',
            'gpl': 'GPLc'
        }
        
        for key, value in fuel_types.items():
            if key in message_lower:
                params['fuel_type'] = value
                break
        
        if 'fuel_type' not in params:
            params['fuel_type'] = 'Gazole'  # Par défaut
        
        # Extraction de la ville ou code postal
        # Chercher un code postal (5 chiffres)
        cp_match = re.search(r'\b\d{5}\b', message)
        if cp_match:
            params['code_postal'] = cp_match.group()
        
        # Chercher une ville (mot en majuscule ou après "à", "dans")
        ville_patterns = [
            r'(?:à|dans|sur)\s+([A-Z][a-zéèêàâôù\-]+(?:\s+[A-Z][a-zéèêàâôù\-]+)*)',
            r'\b([A-Z][a-zéèêàâôù]{3,})\b'
        ]
        
        for pattern in ville_patterns:
            ville_match = re.search(pattern, message)
            if ville_match:
                params['ville'] = ville_match.group(1)
                break
        
        # Limite de résultats
        if any(word in message_lower for word in ['top 3', '3 premiers', 'trois']):
            params['limit'] = 3
        elif any(word in message_lower for word in ['top 5', '5 premiers', 'cinq']):
            params['limit'] = 5
        else:
            params['limit'] = 5
        
        return params
    
    def _search_fuel_prices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recherche les prix de carburant"""
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
            
            return {
                "success": True,
                "fuel_type": fuel_type,
                "location": ville or code_postal,
                "results": results[:10],  # Limiter à 10 résultats
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_cheapest_station(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trouve les stations les moins chères"""
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
            
            return {
                "success": True,
                "fuel_type": fuel_type,
                "location": ville or code_postal,
                "cheapest_stations": results[:limit]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _compare_fuel_prices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare les prix entre plusieurs villes"""
        # À implémenter selon les besoins
        return {"info": "Comparaison non implémentée"}
    
    def _get_fuel_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retourne les statistiques globales"""
        try:
            stats = self.fuel_scraper.get_stats()
            return {
                "success": True,
                "stats": stats
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _detect_scraping(self, params: Dict[str, Any]) -> bool:
        """Détecte si scraping nécessaire"""
        return True
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process complet: détecte l'outil, extrait les params, et exécute
        """
        tool_name = self.detect_tool_needed(message)
        
        if not tool_name:
            return {"tool": None}
        
        params = self._extract_params_from_message(message, tool_name)
        result = self.execute_tool(tool_name, params)
        
        return {
            "tool": tool_name,
            "params": params,
            "result": result
        }


# Tests
if __name__ == "__main__":
    mcp = MCPSimulator()
    
    test_messages = [
        "Quel est le prix du gazole à Paris ?",
        "Trouve-moi les 3 stations les moins chères à Lyon",
        "Donne-moi les stats sur le prix du carburant",
        "Prix de l'essence dans le 75001"
    ]
    
    for msg in test_messages:
        print(f"\n📝 Message: {msg}")
        result = mcp.process_message(msg)
        print(f"🔧 Outil: {result['tool']}")
        if result['tool']:
            print(f"📊 Résultat: {result['result']}")
        print("-" * 50)