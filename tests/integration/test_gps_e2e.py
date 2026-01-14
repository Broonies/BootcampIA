#!/usr/bin/env python3
"""
Test de fin-a-fin de l'integration GPS
Valide que le systeme complet fonctionne correctement apres le refactoring
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.mcp_sim import MCPSimulator


def test_gps_e2e():
    print("\n" + "="*70)
    print("TEST DE FIN A FIN - INTEGRATION GPS (REFACTORED)")
    print("="*70)
    
    mcp = MCPSimulator()
    
    # Simuler les requetes du frontend
    test_cases = [
        {
            "name": "Test 1: Gare depuis Rennes Centre",
            "message": "combien de temps pour aller a la gare en partant de ma position ?",
            "latitude": 48.1150,
            "longitude": -1.6700,
        },
        {
            "name": "Test 2: Universite depuis le sud",
            "message": "De la Gare a Rennes 2 ?",
            "latitude": 48.1050,
            "longitude": -1.6600,
        },
        {
            "name": "Test 3: Place Sainte-Anne",
            "message": "Combien de temps pour aller a la place Sainte-Anne ?",
            "latitude": 48.1104,
            "longitude": -1.6769,
        },
        {
            "name": "Test 4: Prix du carburant",
            "message": "Quel est le prix du gazole a Rennes ?",
            "latitude": 48.1150,
            "longitude": -1.6700,
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{test_case['name']}")
        print(f"  Message: {test_case['message']}")
        print(f"  GPS: ({test_case['latitude']}, {test_case['longitude']})")
        
        try:
            result = mcp.process_message(
                test_case['message'],
                user_location=(test_case['latitude'], test_case['longitude'])
            )
            
            tool_used = result.get("tool")
            params = result.get("params", {})
            tool_result = result.get("result", {})
            
            success = bool(tool_result.get("success")) if "success" in tool_result else True
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status}")
            print(f"  Outil: {tool_used}")
            
            if tool_used == "estimate_drive_time" and success:
                distance = tool_result.get("distance_km", "N/A")
                duration = tool_result.get("duration_minutes", "N/A")
                print(f"  Résultat: {distance} km, {duration} min")
            
            results.append({
                "test": test_case['name'],
                "success": success,
                "tool": tool_used
            })
            
        except Exception as e:
            print(f"  ❌ FAIL - Exception: {str(e)}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ DES TESTS")
    print("="*70)
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"Tests réussis: {passed}/{total}")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['test']}")
    
    return passed == total


def test_drive_time_variants():
    """Test les 6 variantes d'extraction pour les requetes de temps de trajet"""
    print("\n" + "="*70)
    print("TEST DES 6 VARIANTES D'EXTRACTION GPS")
    print("="*70)
    
    mcp = MCPSimulator()
    user_location = (48.1150, -1.6700)  # Rennes Centre
    
    variants = [
        ("de la gare à la place sainte-anne", "Variante 1: 'de X à Y'"),
        ("entre la gare et le palais du parlement", "Variante 2: 'entre X et Y'"),
        ("aller à la gare en partant de ma position", "Variante 3: 'en partant de ma position'"),
        ("pour aller à la gare depuis ma position", "Variante 4: 'depuis ma position'"),
        ("combien de temps pour aller à la place sainte-anne", "Variante 5: simple 'aller à X'"),
    ]
    
    for message, desc in variants:
        print(f"\n{desc}")
        print(f"  Message: '{message}'")
        
        try:
            result = mcp.process_message(message, user_location=user_location)
            tool = result.get("tool")
            params = result.get("params", {})
            
            origin = params.get("origin_name", "N/A")
            dest = params.get("destination_name", "N/A")
            
            print(f"  Outil: {tool}")
            print(f"  Origine: {origin}")
            print(f"  Destination: {dest}")
            
            if tool == "estimate_drive_time" and origin and dest:
                print(f"  ✅ Extraction réussie")
            else:
                print(f"  ❌ Extraction échouée")
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")


if __name__ == "__main__":
    # Test principal
    all_passed = test_gps_e2e()
    
    # Test des variantes
    test_drive_time_variants()
    
    # Résultat final
    print("\n" + "="*70)
    if all_passed:
        print("✅ TOUS LES TESTS SONT PASSÉS!")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
    print("="*70 + "\n")
