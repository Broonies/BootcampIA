"""Tests unitaires pour la classe ToolDetector"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.tool_detector import ToolDetector


def test_detect_fuel_query():
    """Test de détection des requêtes de prix de carburant"""
    detector = ToolDetector()
    
    test_cases = [
        ("quel est le prix du gazole ?", "search_fuel_prices"),
        ("trouve les stations les moins chères", "get_cheapest_station"),
        ("donne moi les stats sur le carburant", "get_fuel_stats"),
    ]
    
    print("\n[TEST] ToolDetector - Fuel queries")
    for message, expected in test_cases:
        result = detector.detect(message)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"  {status} '{message}' -> {result}")
        assert result == expected, f"Expected {expected}, got {result}"


def test_detect_drive_time_query():
    """Test de détection des requêtes de temps de trajet"""
    detector = ToolDetector()
    
    test_cases = [
        ("combien de temps pour aller à la gare ?", "estimate_drive_time"),
        ("de la gare à rennes 2", "estimate_drive_time"),
        ("combien de temps en partant de ma position ?", "estimate_drive_time"),
    ]
    
    print("\n[TEST] ToolDetector - Drive time queries")
    for message, expected in test_cases:
        result = detector.detect(message)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"  {status} '{message}' -> {result}")
        assert result == expected, f"Expected {expected}, got {result}"


def test_detect_traffic_query():
    """Test de détection des requêtes de statut du trafic"""
    detector = ToolDetector()
    
    test_cases = [
        ("quel est le trafic ?", "get_traffic_status"),
        ("y a des bouchons ?", "get_traffic_status"),
    ]
    
    print("\n[TEST] ToolDetector - Traffic queries")
    for message, expected in test_cases:
        result = detector.detect(message)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"  {status} '{message}' -> {result}")
        assert result == expected, f"Expected {expected}, got {result}"


def test_detect_parking_query():
    """Test de détection des requêtes de parking"""
    detector = ToolDetector()
    
    test_cases = [
        ("où sont les parkings ?", "get_parking_status"),
        ("y a de la place pour me garer ?", "get_parking_status"),
    ]
    
    print("\n[TEST] ToolDetector - Parking queries")
    for message, expected in test_cases:
        result = detector.detect(message)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"  {status} '{message}' -> {result}")
        assert result == expected, f"Expected {expected}, got {result}"


if __name__ == "__main__":
    test_detect_fuel_query()
    test_detect_drive_time_query()
    test_detect_traffic_query()
    test_detect_parking_query()
    print("\n[OK] Tous les tests ToolDetector réussis !")
