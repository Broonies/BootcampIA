# backend/app/config.py
"""
Configuration pour l'assistant mobilité Rennes
"""

# Zone géographique ciblée
RENNES_CITY = "rennes"
RENNES_POSTAL_CODES = ["35000", "35200", "35700"]  # Codes postaux de Rennes
RENNES_METRO_POSTAL_CODES = [
    "35000", "35200", "35700",  # Rennes
    "35510", "35170", "35650",  # Cesson-Sévigné, Bruz, Le Rheu
    "35850", "35235", "35590",  # Betton, Thorigné-Fouillard, Saint-Gilles
]

# Coordonnées de Rennes (centre-ville)
RENNES_LAT = 48.1173
RENNES_LON = -1.6778
RENNES_RADIUS_KM = 15  # Rayon en km autour du centre

# Filtres de recherche
DEFAULT_FUEL_TYPE = "Gazole"
MAX_RESULTS = 5
