"""
Table de correspondance des lieux emblématiques de Rennes et sa métropole
Coordonnées GPS (latitude, longitude)
Fichier local plus rapide qu'une API externe et Hors-ligne, pour tester notre POC.

Features:
- find_location(): Recherche exacte (rapide)
- find_location_fuzzy(): Recherche floue avec tolérance aux typos/accents
- get_suggestions(): Suggestions intelligentes par fuzzy matching
"""

from difflib import get_close_matches
import unicodedata

# Dictionnaire principal avec tous les lieux de Rennes Métropole
RENNES_LOCATIONS = {
    # Centre-ville et quartiers principaux
    'rennes': (48.1113, -1.6800),
    'rennes centre': (48.1113, -1.6800),
    'centre rennes': (48.1113, -1.6800),
    'centre ville': (48.1113, -1.6800),
    'centre-ville': (48.1113, -1.6800),
    'hypercentre': (48.1113, -1.6800),
    
    # Quartiers de Rennes
    'cleunay': (48.1030, -1.7030),
    'villejean': (48.1230, -1.7080),
    'maurepas': (48.0950, -1.6570),
    'patton': (48.1020, -1.6950),
    'bréquigny': (48.0920, -1.6580),
    'brequigny': (48.0920, -1.6580),
    'beauregard': (48.1170, -1.6390),
    'francisco ferrer': (48.1100, -1.6340),
    'beaulieu': (48.1180, -1.6330),
    'gay lussac': (48.1200, -1.6720),
    'thabor': (48.1130, -1.6650),
    'jeanne d arc': (48.1070, -1.6780),
    'jeanne d\'arc': (48.1070, -1.6780),
    'saint hélier': (48.1050, -1.6430),
    'saint helier': (48.1050, -1.6430),
    'vern': (48.0450, -1.6070),
    
    # Universités et établissements
    'université rennes 1': (48.1170, -1.6380),
    'universite rennes 1': (48.1170, -1.6380),  # Variante sans accent
    'université rennes 2': (48.1238, -1.7080),
    'universite rennes 2': (48.1238, -1.7080),  # Variante sans accent
    'rennes 1': (48.1170, -1.6380),
    'rennes 2': (48.1238, -1.7080),
    'villejean université': (48.1238, -1.7080),
    'villejean universite': (48.1238, -1.7080),  # Variante sans accent
    'campus beaulieu': (48.1180, -1.6330),
    'campus villejean': (48.1238, -1.7080),
    'insa': (48.1200, -1.6380),
    'insa rennes': (48.1200, -1.6380),
    'sciences po': (48.1150, -1.7050),
    'sciences po rennes': (48.1150, -1.7050),
    
    # Lieux emblématiques
    'gare': (48.1039, -1.6720),
    'gare sncf': (48.1039, -1.6720),
    'gare de rennes': (48.1039, -1.6720),
    'mail françois mitterrand': (48.1050, -1.6795),
    'mail mitterrand': (48.1050, -1.6795),
    'mail': (48.1050, -1.6795),
    'république': (48.1100, -1.6780),
    'republique': (48.1100, -1.6780),
    'place de la république': (48.1100, -1.6780),
    'place de la republique': (48.1100, -1.6780),
    'place des lices': (48.1140, -1.6820),
    'lices': (48.1140, -1.6820),
    'marché des lices': (48.1140, -1.6820),
    'parlement de bretagne': (48.1113, -1.6830),
    'parlement': (48.1113, -1.6830),
    'place du parlement': (48.1113, -1.6830),
    'hôtel de ville': (48.1113, -1.6770),
    'hotel de ville': (48.1113, -1.6770),
    'mairie': (48.1113, -1.6770),
    'thabor parc': (48.1130, -1.6650),
    'parc du thabor': (48.1130, -1.6650),
    'colombier': (48.1145, -1.6860),
    'place sainte anne': (48.1120, -1.6810),
    'place sainte-anne': (48.1120, -1.6810),
    'place saint anne': (48.1120, -1.6810),
    'place saint-anne': (48.1120, -1.6810),
    'saint anne': (48.1120, -1.6810),
    'sainte anne': (48.1120, -1.6810),
    'saint-anne': (48.1120, -1.6810),
    'sainte-anne': (48.1120, -1.6810),
    
    # Pôles commerciaux
    'alma': (48.1050, -1.6460),
    'centre alma': (48.1050, -1.6460),
    'colombia': (48.1020, -1.7090),
    'centre colombia': (48.1020, -1.7090),
    'cesson commercial': (48.0920, -1.6050),
    
    # Hôpitaux
    'chu': (48.1110, -1.6680),
    'chu pontchaillou': (48.1110, -1.6680),
    'pontchaillou': (48.1110, -1.6680),
    'hopital sud': (48.0830, -1.6730),
    'hôpital sud': (48.0830, -1.6730),
    'clinique saint laurent': (48.1090, -1.6510),
    
    # Communes de la métropole
    'betton': (48.1394, -1.6203),
    'cesson sévigné': (48.0933, -1.6500),
    'cesson sevigne': (48.0933, -1.6500),
    'cesson': (48.0933, -1.6500),
    'saint grégoire': (48.1520, -1.6830),
    'saint gregoire': (48.1520, -1.6830),
    'chantepie': (48.0890, -1.6180),
    'bruz': (48.0250, -1.7500),
    'chartres de bretagne': (48.0450, -1.6990),
    'pacé': (48.1450, -1.7600),
    'pace': (48.1450, -1.7600),
    'thorigné fouillard': (48.1550, -1.5750),
    'thorigne fouillard': (48.1550, -1.5750),
    'thorigne': (48.1550, -1.5750),
    'vern sur seiche': (48.0450, -1.6070),
    'vern': (48.0450, -1.6070),
    'acigné': (48.1330, -1.5380),
    'acigne': (48.1330, -1.5380),
    'mordelles': (48.0750, -1.8460),
    'saint jacques de la lande': (48.0750, -1.7170),
    'saint jacques': (48.0750, -1.7170),
    
    # Destinations externes proches
    'saint malo': (48.6500, -2.0267),
    'saint-malo': (48.6500, -2.0267),
    'dinard': (48.6340, -2.0570),
    'fougères': (48.3530, -1.2020),
    'fougeres': (48.3530, -1.2020),
    'vitré': (48.1250, -1.2100),
    'vitre': (48.1250, -1.2100),
    'redon': (47.6510, -2.0840),
    'nantes': (47.2184, -1.5536),
}


def find_location(location_name: str) -> tuple:
    """
    Recherche une localisation par son nom (insensible à la casse)
    Args:
        location_name: Nom du lieu recherché
        
    Returns:
        Tuple (latitude, longitude) ou None si non trouvé
    """
    return RENNES_LOCATIONS.get(location_name.lower())


def _remove_accents(text: str) -> str:
    """Supprime les accents d'une chaîne"""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


def find_location_fuzzy(location_name: str, threshold: float = 0.75) -> tuple:
    """
    Recherche floue d'une localisation avec tolérance aux typos/accents
    
    Stratégie:
    1. Essayer un match exact d'abord (rapide)
    2. Essayer sans accents
    3. Fuzzy matching sur les clés
    
    Args:
        location_name: Nom du lieu recherché (peut contenir typos)
        threshold: Seuil de similarité (0-1). 0.75 = 75% de similitude
        
    Returns:
        Tuple (latitude, longitude) ou None si non trouvé
        
    Examples:
        >>> find_location_fuzzy("universite rennes 2")  # Pas d'accent
        (48.1238, -1.7080)
        
        >>> find_location_fuzzy("univ rennes 2")  # Abréviation
        (48.1238, -1.7080)
        
        >>> find_location_fuzzy("garr")  # Typo
        (48.1039, -1.6720)  # la gare
    """
    clean_name = location_name.lower().strip()
    
    # 1. Match exact
    if clean_name in RENNES_LOCATIONS:
        return RENNES_LOCATIONS[clean_name]
    
    # 2. Match sans accents
    clean_no_accents = _remove_accents(clean_name)
    for key, coords in RENNES_LOCATIONS.items():
        if _remove_accents(key) == clean_no_accents:
            return coords
    
    # 3. Fuzzy matching sur les clés
    all_keys = list(RENNES_LOCATIONS.keys())
    closest_matches = get_close_matches(clean_name, all_keys, n=1, cutoff=threshold)
    
    if closest_matches:
        matched_key = closest_matches[0]
        return RENNES_LOCATIONS[matched_key]
    
    return None


def get_known_locations() -> list:
    """Retourne la liste de tous les lieux connus"""
    return sorted(RENNES_LOCATIONS.keys())


def get_suggestions(partial_name: str, limit: int = 5) -> list:
    """
    Retourne des suggestions de lieux intelligentes
    
    Stratégie:
    1. Recherche par sous-chaîne exacte
    2. Fuzzy matching si trop peu de résultats
    
    Args:
        partial_name: Début du nom recherché (peut contenir typos)
        limit: Nombre maximum de suggestions
        
    Returns:
        Liste de noms de lieux correspondants
        
    Examples:
        >>> get_suggestions("rennes")
        ['rennes', 'rennes centre', 'rennes 1', 'rennes 2', ...]
        
        >>> get_suggestions("univ")  # Abréviation
        ['université rennes 1', 'université rennes 2', ...]
    """
    partial_lower = partial_name.lower().strip()
    
    # 1. Recherche par sous-chaîne
    substring_matches = [
        name for name in RENNES_LOCATIONS.keys()
        if partial_lower in name
    ]
    
    if len(substring_matches) >= limit:
        return sorted(substring_matches)[:limit]
    
    # 2. Fuzzy matching si pas assez de résultats
    all_keys = list(RENNES_LOCATIONS.keys())
    fuzzy_matches = get_close_matches(partial_lower, all_keys, n=limit, cutoff=0.6)
    
    # Combiner et dédupliquer
    combined = list(dict.fromkeys(substring_matches + fuzzy_matches))
    
    # 3. Si toujours aucun résultat, suggérer les lieux les plus populaires
    if not combined:
        popular_places = [
            'rennes', 'gare', 'république', 'place des lices', 
            'université rennes 1', 'université rennes 2', 'chu',
            'centre ville', 'villejean', 'beaulieu'
        ]
        return popular_places[:limit]
    
    return sorted(combined)[:limit]
