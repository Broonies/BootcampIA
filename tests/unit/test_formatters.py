"""Tests unitaires pour les formateurs"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.formatters import (
    format_fuel_results,
    format_traffic_results,
    format_parking_results,
    format_drive_time_results,
)


def test_format_fuel_results():
    """Test de formatage des résultats de carburant"""
    mock_result = {
        "tool": "search_fuel_prices",
        "result": {
            "success": True,
            "fuel_type": "Gazole",
            "location": "Rennes",
            "count": 1,
            "results": [
                {
                    "adresse": "123 Rue de Rennes",
                    "ville": "Rennes",
                    "cp": "35000",
                    "fuel_type": "Gazole",
                    "price": 1.45,
                    "updated": "2026-01-14"
                }
            ]
        }
    }
    
    print("\n[TEST] Formatters - Fuel results")
    formatted = format_fuel_results(mock_result)
    assert isinstance(formatted, str), "Formatted result should be string"
    assert "Rennes" in formatted, "Formatted result should contain city name"
    assert "1.45" in formatted, "Formatted result should contain price"
    print(f"  [OK] Formatted fuel results: {formatted[:100]}...")


def test_format_drive_time_results():
    """Test de formatage des résultats de temps de trajet"""
    mock_result = {
        "tool": "estimate_drive_time",
        "result": {
            "success": True,
            "distance_km": 2.5,
            "duration_minutes": 8.5,
        }
    }
    
    print("\n[TEST] Formatters - Drive time results")
    formatted = format_drive_time_results(mock_result)
    assert isinstance(formatted, str), "Formatted result should be string"
    assert "2.5" in formatted or "distance" in formatted.lower(), "Should contain distance info"
    print(f"  [OK] Formatted drive time: {formatted[:100]}...")


def test_format_parking_results():
    """Test de formatage des résultats de parking"""
    mock_result = {
        "tool": "get_parking_status",
        "result": {
            "success": True,
            "parkings": [
                {
                    "name": "Parking A",
                    "available": 45,
                    "total": 100,
                    "status": "🟡 Places disponibles",
                    "location": "48.1000, -1.6000",
                    "occupancy_rate": 55.0
                }
            ],
            "updated": "14:30",
            "total_parkings": 1
        }
    }
    
    print("\n[TEST] Formatters - Parking results")
    formatted = format_parking_results(mock_result)
    assert isinstance(formatted, str), "Formatted result should be string"
    assert "Parking A" in formatted, "Formatted result should contain parking name"
    assert "45" in formatted, "Formatted result should contain available spaces"
    print(f"  [OK] Formatted parking results: {formatted[:100]}...")


def test_format_traffic_results():
    """Test de formatage des résultats de trafic"""
    mock_result = {
        "tool": "get_traffic_status",
        "result": {
            "success": True,
            "traffic_info": "Circulation normale"
        }
    }
    
    print("\n[TEST] Formatters - Traffic results")
    formatted = format_traffic_results(mock_result)
    assert isinstance(formatted, str), "Formatted result should be string"
    print(f"  [OK] Formatted traffic results: {formatted[:100]}...")


if __name__ == "__main__":
    test_format_fuel_results()
    test_format_drive_time_results()
    test_format_parking_results()
    test_format_traffic_results()
    print("\n[OK] Tous les tests de formateurs réussis !")
