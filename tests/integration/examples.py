#!/usr/bin/env python3
"""
Exemples d'utilisation des composants refactorisés
Démontre comment utiliser ToolDetector, ParamExtractor, ToolExecutor et MCPSimulator
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.tool_detector import ToolDetector
from backend.app.param_extractor import ParamExtractor
from backend.app.tool_executor import ToolExecutor
from backend.app.mcp_sim import MCPSimulator


def example_individual_components():
    """Exemple d'utilisation des composants individuels"""
    print("\n" + "="*70)
    print("EXEMPLE: UTILISATION DES COMPOSANTS INDIVIDUELS")
    print("="*70)
    
    # 1. ToolDetector
    print("\n[1] TOOL DETECTOR")
    detector = ToolDetector()
    message = "Quel est le prix du gazole à Rennes ?"
    tool = detector.detect(message)
    print(f"  Message: {message}")
    print(f"  Outil détecté: {tool}")
    
    # 2. ParamExtractor
    print("\n[2] PARAM EXTRACTOR")
    extractor = ParamExtractor()
    params = extractor.extract(message, tool)
    print(f"  Paramètres extraits: {params}")
    
    # 3. ToolExecutor
    print("\n[3] TOOL EXECUTOR")
    executor = ToolExecutor()
    result = executor.execute(tool, params)
    print(f"  Résultat (extrait): {str(result)[:200]}...")


def example_mcp_simulator():
    """Exemple d'utilisation du MCPSimulator (orchestrateur)"""
    print("\n" + "="*70)
    print("EXEMPLE: UTILISATION DU MCP SIMULATOR (ORCHESTRATEUR)")
    print("="*70)
    
    mcp = MCPSimulator()
    
    queries = [
        {
            "message": "Quel est le prix du gazole à Rennes ?",
            "location": None
        },
        {
            "message": "Combien de temps pour aller à la gare ?",
            "location": (48.1150, -1.6700)
        },
        {
            "message": "Y a des parkings disponibles ?",
            "location": None
        }
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query['message']}")
        if query['location']:
            print(f"📍 GPS: {query['location']}")
        
        result = mcp.process_message(query['message'], user_location=query['location'])
        
        print(f"🔧 Outil: {result['tool']}")
        print(f"📊 Résultat (extrait): {str(result['result'])[:200]}...")


def example_gps_integration():
    """Exemple d'intégration GPS complète"""
    print("\n" + "="*70)
    print("EXEMPLE: INTÉGRATION GPS COMPLÈTE")
    print("="*70)
    
    mcp = MCPSimulator()
    
    # Simuler une position utilisateur
    user_position = (48.1150, -1.6700)  # Rennes Centre
    
    print(f"\n👤 Position utilisateur: {user_position}")
    
    # Requête avec "ma position"
    message = "Combien de temps pour aller à la place Sainte-Anne en partant de ma position ?"
    print(f"\n📱 Message: {message}")
    
    result = mcp.process_message(message, user_location=user_position)
    
    tool = result['tool']
    params = result['params']
    exec_result = result['result']
    
    print(f"\n✅ Résultat:")
    print(f"  - Outil: {tool}")
    print(f"  - Origine: {params.get('origin_name')}")
    print(f"  - Destination: {params.get('destination_name')}")
    
    if exec_result.get("success"):
        print(f"  - Distance: {exec_result.get('distance_km')} km")
        print(f"  - Durée: {exec_result.get('duration_minutes')} min")
    else:
        print(f"  - Erreur: {exec_result.get('error')}")


if __name__ == "__main__":
    example_individual_components()
    example_mcp_simulator()
    example_gps_integration()
    print("\n" + "="*70)
    print("✅ Exemples terminés!")
    print("="*70 + "\n")
