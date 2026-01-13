import requests
import json

def get_parking_rennes():
    """
    Récupère les places de parking disponibles en temps réel à Rennes.
    Source: API Open Data Rennes Métropole.
    """
    # L'URL officielle de l'API v2.1
    url = "https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/export-api-parking-citedia/records?limit=20"

    print("🅿️  Interrogation de l'API Parking Rennes...")

    try:
        response = requests.get(url)
        response.raise_for_status() # Vérifie s'il y a une erreur HTTP (404, 500...)
        
        data = response.json()
        
        # On prépare une liste propre pour l'IA
        parkings_clean = []

        # On boucle sur chaque résultat trouvé
        for record in data.get("results", []):
            infos = record  # Les données sont directes en v2.1
            
            # On extrait juste ce qui nous intéresse
            # (Nom, État, Places libres / Total)
            nom = infos.get("key", "Inconnu")
            etat = infos.get("status", "INCONNU")
            places_libres = infos.get("free", 0)
            capacite_totale = infos.get("max", 0)

            # On crée un petit résumé textuel pour l'IA
            parkings_clean.append({
                "nom": nom,
                "etat": etat, # OUVERT ou FERME
                "disponibilite": f"{places_libres} places libres sur {capacite_totale}",
                "taux_remplissage": f"{round((1 - places_libres/max(capacite_totale, 1)) * 100)}%"
            })

        # On renvoie le tout en JSON texte
        return json.dumps(parkings_clean, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Impossible de contacter l'API Rennes: {str(e)}"})

# Zone de test
if __name__ == "__main__":
    print(get_parking_rennes())