"""Tests unitaires pour la classe ParamExtractor"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.param_extractor import ParamExtractor


def test_extract_fuel_type():
    """Test d'extraction du type de carburant"""
    extractor = ParamExtractor()
    
    test_cases = [
        ("quel est le prix du gazole ?", "Gazole"),
        ("prix du sp95", "SP95"),
        ("essence sp98", "SP98"),
        ("prix e10", "E10"),
        ("carburant par defaut", "Gazole"),  # Default
    ]
    
    print("\n[TEST] ParamExtractor - Fuel type extraction")
    for message, expected in test_cases:
        params = extractor.extract(message, "search_fuel_prices")
        fuel_type = params.get("fuel_type", "Gazole")
        status = "[OK]" if fuel_type == expected else "[FAIL]"
        print(f"  {status} '{message}' -> {fuel_type}")
        assert fuel_type == expected, f"Expected {expected}, got {fuel_type}"


def test_extract_drive_time_params():
    """Test d'extraction des paramètres de temps de trajet"""
    extractor = ParamExtractor()
    
    test_cases = [
        ("de la gare à rennes 2", "gare", "rennes 2"),
        ("entre la gare et rennes 2", "gare", "rennes 2"),
        ("aller à la place sainte-anne", "ma position", "place sainte-anne"),
    ]
    
    print("\n[TEST] ParamExtractor - Drive time parameter extraction")
    for message, expected_origin, expected_dest in test_cases:
        params = extractor.extract(message, "estimate_drive_time")
        origin = params.get("origin_name", "").lower()
        dest = params.get("destination_name", "").lower()
        
        origin_match = expected_origin.lower() in origin
        dest_match = expected_dest.lower() in dest
        status = "[OK]" if (origin_match and dest_match) else "[FAIL]"
        
        print(f"  {status} '{message}'")
        print(f"      Origin: {origin} (expected to contain '{expected_origin}')")
        print(f"      Dest: {dest} (expected to contain '{expected_dest}')")


def test_extract_location():
    """Test d'extraction de localisation"""
    extractor = ParamExtractor()
    
    test_cases = [
        ("prix du gazole à rennes", "Rennes"),
        ("gazole dans rennes", "Rennes"),
        ("carburant code postal 35000", "35000"),
    ]
    
    print("\n[TEST] ParamExtractor - Location extraction")
    for message, expected_location in test_cases:
        params = extractor.extract(message, "search_fuel_prices")
        location = params.get("ville") or params.get("code_postal")
        status = "[OK]" if location and expected_location in location else "[FAIL]"
        print(f"  {status} '{message}' -> {location}")


if __name__ == "__main__":
    test_extract_fuel_type()
    test_extract_drive_time_params()
    test_extract_location()
    print("\n[OK] Tous les tests ParamExtractor réussis !")
