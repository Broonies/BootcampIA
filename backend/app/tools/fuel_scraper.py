# backend/app/fuel_scraper.py

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
import zipfile
import io

# Codes postaux Rennes Métropole
RENNES_METRO_POSTAL_CODES = [
    "35000", "35200", "35700",  # Rennes
    "35510", "35170", "35650",  # Cesson-Sévigné, Bruz, Le Rheu
    "35850", "35235", "35590",  # Betton, Thorigné-Fouillard, Saint-Gilles
]

def safe_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

class FuelPriceScraper:
    """
    Scraper pour les prix des carburants depuis donnees.roulez-eco.fr
    Données open-data officielles (ZIP -> XML)
    Cache local optionnel
    """

    def __init__(self, cache_dir: str = "cache", restrict_to_rennes: bool = True):
        self.base_url = "https://donnees.roulez-eco.fr/opendata/jour"
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "fuel_prices_cache.json")
        self.restrict_to_rennes = restrict_to_rennes

        os.makedirs(cache_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # CACHE
    # ------------------------------------------------------------------

    def _get_cache(self) -> Optional[Dict]:
        if not os.path.exists(self.cache_file):
            return None

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)

            timestamp = datetime.fromisoformat(cache["timestamp"])
            if datetime.now() - timestamp < timedelta(hours=24):
                print(f"[Cache] Cache valide ({timestamp})")
                return cache["data"]

            return None
        except Exception as e:
            print("[Warning] Erreur lecture cache:", e)
            return None

    def _save_cache(self, data: Dict):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "data": data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"[Cache] Cache sauvegarde ({data['total_stations']} stations)")

    # ------------------------------------------------------------------
    # FETCH
    # ------------------------------------------------------------------

    def fetch_daily_prices(self, force_refresh: bool = False) -> Dict:
        if not force_refresh:
            cached = self._get_cache()
            if cached:
                return cached

        print("[Download] Telechargement des prix carburants...")

        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()

            # ----------------------------------------------------------
            # ⚠️ L'API renvoie un ZIP, PAS du XML
            # ----------------------------------------------------------
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                xml_files = [f for f in z.namelist() if f.endswith(".xml")]
                if not xml_files:
                    raise ValueError("Aucun fichier XML trouvé dans l'archive")

                xml_content = z.read(xml_files[0])

            root = ET.fromstring(xml_content)

            stations = []

            for pdv in root.findall("pdv"):
                lat = safe_float(pdv.get("latitude")) / 100000
                lon = safe_float(pdv.get("longitude")) / 100000

                station = {
    "id": pdv.get("id"),
    "latitude": lat,
    "longitude": lon,
    "cp": pdv.get("cp", ""),
    "ville": "",
    "adresse": "",
    "prices": {},
}

                adresse = pdv.find("adresse")
                if adresse is not None and adresse.text:
                    station["adresse"] = adresse.text.strip()

                ville = pdv.find("ville")
                if ville is not None and ville.text:
                    station["ville"] = ville.text.strip()

                for prix in pdv.findall("prix"):
                    carburant = prix.get("nom")
                    valeur = prix.get("valeur")
                    maj = prix.get("maj")

                    if carburant and valeur:
                        station["prices"][carburant] = {
                            "price": float(valeur),
                            "updated": maj,
                        }

                stations.append(station)

            result = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_stations": len(stations),
                "stations": stations,
            }

            self._save_cache(result)
            print(f"[Success] {len(stations)} stations chargees")

            return result

        except Exception as e:
            print("[Error] Erreur recuperation carburants:", e)
            cached = self._get_cache()
            if cached:
                print("[Warning] Utilisation du cache existant")
                return cached
            raise

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------

    def search_by_city(
        self, ville: str, fuel_type: str = "Gazole"
    ) -> List[Dict]:
        data = self.fetch_daily_prices()
        ville_original = ville
        ville = ville.lower()

        # 🔒 RESTRICTION Ille-et-Vilaine (35) si activée
        if self.restrict_to_rennes and not ville.startswith("35") and "rennes" not in ville:
            print(f"[Warning] Restriction Ille-et-Vilaine : recherche limitee au departement 35 (demande: {ville_original})")
            ville = "rennes"

        results = []
        for s in data["stations"]:
            # Filtrer par département 35 si restriction
            if self.restrict_to_rennes and not s["cp"].startswith("35"):
                continue
            
            if ville in s["ville"].lower():
                if fuel_type in s["prices"]:
                    results.append(
                        {
                            "ville": s["ville"],
                            "adresse": s["adresse"],
                            "cp": s["cp"],
                            "fuel_type": fuel_type,
                            "price": s["prices"][fuel_type]["price"],
                            "updated": s["prices"][fuel_type]["updated"],
                        }
                    )

        results.sort(key=lambda x: x["price"])
        return results

    def search_by_postal_code(
        self, cp: str, fuel_type: str = "Gazole"
    ) -> List[Dict]:
        data = self.fetch_daily_prices()

        # 🔒 RESTRICTION Ille-et-Vilaine (35) si activée
        if self.restrict_to_rennes:
            cp_valid = cp.startswith("35")
            if not cp_valid:
                print(f"[Warning] CP {cp} hors Ille-et-Vilaine - recherche limitee au departement 35")
                cp = "35"

        results = []
        for s in data["stations"]:
            # Double filtre si restriction active
            if self.restrict_to_rennes and not s["cp"].startswith("35"):
                continue
            
            if s["cp"].startswith(cp):
                if fuel_type in s["prices"]:
                    results.append(
                        {
                            "ville": s["ville"],
                            "adresse": s["adresse"],
                            "cp": s["cp"],
                            "fuel_type": fuel_type,
                            "price": s["prices"][fuel_type]["price"],
                            "updated": s["prices"][fuel_type]["updated"],
                        }
                    )

        results.sort(key=lambda x: x["price"])
        return results

    def get_cheapest_in_city(
        self, ville: str, fuel_type: str = "Gazole", limit: int = 5
    ) -> List[Dict]:
        return self.search_by_city(ville, fuel_type)[:limit]

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict:
        data = self.fetch_daily_prices()

        # 🔒 RESTRICTION RENNES si activée
        stations = data["stations"]
        if self.restrict_to_rennes:
            stations = [
                s for s in stations
                if any(s["cp"].startswith(cp) for cp in RENNES_METRO_POSTAL_CODES)
            ]

        prices = [
            s["prices"]["Gazole"]["price"]
            for s in stations
            if "Gazole" in s["prices"]
        ]

        if not prices:
            return {"error": "Aucune donnée Gazole"}

        location_info = "Rennes Métropole" if self.restrict_to_rennes else "France"
        return {
            "date": data["date"],
            "location": location_info,
            "total_stations": len(stations),
            "gazole": {
                "min": min(prices),
                "max": max(prices),
                "avg": round(sum(prices) / len(prices), 3),
            },
        }


# ----------------------------------------------------------------------
# TEST LOCAL
# ----------------------------------------------------------------------
if __name__ == "__main__":
    scraper = FuelPriceScraper()

    print("\n=== TEST RÉCUPÉRATION ===")
    data = scraper.fetch_daily_prices(force_refresh=True)
    print("Stations:", data["total_stations"])

    print("\n=== RENNES - GAZOLE ===")
    rennes = scraper.get_cheapest_in_city("Rennes", "Gazole", 5)
    for i, s in enumerate(rennes, 1):
        print(f"{i}. {s['adresse']} – {s['price']} €")

    print("\n=== STATS ===")
    print(json.dumps(scraper.get_stats(), indent=2, ensure_ascii=False))