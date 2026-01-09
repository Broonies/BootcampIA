import re

class MCPSimulator:
    """
    Simule un serveur MCP avec détection d'outils nécessaires
    """
    
    def __init__(self):
        # FIX: Utiliser un dict simple, pas de set
        self.tools = {
            "scrape_website": "scrape",
            "search_web": "search",
        }
    
    def detect_tool_needed(self, user_message: str) -> str | None:
        """
        Détecte si un outil est nécessaire basé sur le message utilisateur
        """
        message_lower = user_message.lower()
        
        # Détection de scraping
        if re.search(r'https?://\S+', user_message):
            return "scrape_website"
        
        if any(keyword in message_lower for keyword in ['scrape', 'récupère', 'extrait', 'site web', 'page']):
            return "scrape_website"
        
        # Détection de recherche web
        if any(keyword in message_lower for keyword in ['recherche', 'trouve', 'cherche', 'google']):
            return "search_web"
        
        return None