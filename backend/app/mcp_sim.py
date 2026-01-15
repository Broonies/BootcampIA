# backend/app/mcp_sim.py
"""Simulateur MCP - Orchestre la détection, l'extraction et l'exécution des outils."""
from typing import Optional, Dict, Any

from .tool_detector import ToolDetector
from .param_extractor import ParamExtractor
from .tool_executor import ToolExecutor


class MCPSimulator:
    """
    Orchestrateur MCP - Coordonne la détection, l'extraction et l'exécution d'outils.
    """
    
    def __init__(self):
        self.detector = ToolDetector()
        self.extractor = ParamExtractor()
        self.executor = ToolExecutor()
    
    def process_message(self, user_message: str, user_location: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Traite un message utilisateur : détecte l'outil, extrait les paramètres, et exécute l'outil.
        
        Args:
            user_message: Message de l'utilisateur
            user_location: Position GPS optionnelle (latitude, longitude)
            
        Returns:
            Résultat contenant l'outil détecté, les paramètres, et le résultat
        """
        print(f"\n[MCP] Message: {user_message}")
        print(f"[MCP] User location: {user_location}")
        
        # 1. Détection de l'outil
        tool_name = self.detector.detect(user_message)
        if not tool_name:
            print("[MCP] Aucun outil détecté")
            return {
                "tool": None,
                "params": {},
                "result": {"error": "Je ne comprends pas votre demande"}
            }
        
        print(f"[MCP] Outil détecté: {tool_name}")
        
        # 2. Extraction des paramètres
        params = self.extractor.extract(user_message, tool_name)
        print(f"[MCP] Paramètres extraits: {params}")
        
        # 3. Exécution de l'outil avec position GPS
        result = self.executor.execute(tool_name, params, user_location)
        print(f"[MCP] Résultat: {result}")
        
        return {
            "tool": tool_name,
            "params": params,
            "result": result
        }

 