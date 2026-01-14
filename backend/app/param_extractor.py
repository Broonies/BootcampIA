"""Extraction de paramètres pour les outils MCP."""
import re
from typing import Dict, Any


class ParamExtractor:
    """Extrait les paramètres des messages utilisateur pour des outils spécifiques."""
    
    def extract(self, message: str, tool_name: str) -> Dict[str, Any]:
        """
        Extrait les paramètres du message selon l'outil détecté.
        
        Args:
            message: Message de l'utilisateur
            tool_name: Nom de l'outil détecté
            
        Returns:
            Dictionnaire des paramètres extraits
        """
        message_lower = message.lower()
        params = {}
        
        # Extraction commune : fuel_type
        params.update(self._extract_fuel_type(message_lower))
        
        # Extraction commune : ville/code_postal
        params.update(self._extract_location(message))
        
        # Extraction spécifique selon l'outil
        if tool_name == 'estimate_drive_time':
            params.update(self._extract_drive_time_params(message, message_lower))
        elif tool_name == 'get_traffic_status':
            params.update(self._extract_traffic_params(message))
        
        # Extraction limite de résultats
        params.update(self._extract_result_limit(message_lower))
        
        return params
    
    def _extract_fuel_type(self, message_lower: str) -> Dict[str, str]:
        """Extrait le type de carburant."""
        fuel_types = {
            'gazole': 'Gazole',
            'diesel': 'Gazole',
            'sp95': 'SP95',
            'sp98': 'SP98',
            'e10': 'E10',
            'e85': 'E85',
            'gpl': 'GPLc'
        }
        
        for key, value in fuel_types.items():
            if key in message_lower:
                return {'fuel_type': value}
        
        return {'fuel_type': 'Gazole'}  # Par défaut
    
    def _extract_location(self, message: str) -> Dict[str, str]:
        """Extrait la ville ou le code postal."""
        params = {}
        
        # Chercher un code postal (5 chiffres)
        cp_match = re.search(r'\b\d{5}\b', message)
        if cp_match:
            params['code_postal'] = cp_match.group()
        
        # Chercher une ville (mot en majuscule ou après "à", "dans")
        ville_patterns = [
            r'(?:à|dans|sur)\s+([A-Z][a-zéèêàâôù\-]+(?:\s+[A-Z][a-zéèêàâôù\-]+)*)',
            r'\b([A-Z][a-zéèêàâôù]{3,})\b'
        ]
        
        for pattern in ville_patterns:
            ville_match = re.search(pattern, message)
            if ville_match:
                params['ville'] = ville_match.group(1)
                break
        
        # Défaut : département 35 si aucune localisation fournie
        if 'code_postal' not in params and 'ville' not in params:
            params['code_postal'] = '35'
            params['ville'] = 'Rennes'
        
        return params
    
    def _extract_traffic_params(self, message: str) -> Dict[str, str]:
        """Extrait les paramètres pour le trafic (nom de rue)."""
        params = {}
        
        street_patterns = [
            r"(?:rue|avenue|av\.?|boulevard|bd\.?|quai|route|chemin|allee|impasse|place)\s+([A-Za-zÀ-ÿ'\- ]{3,})",
            r'"([^"]{3,})"',
        ]
        
        for pat in street_patterns:
            m = re.search(pat, message, flags=re.IGNORECASE)
            if m:
                params['street_query'] = m.group(1).strip()
                break
        
        return params
    
    def _extract_drive_time_params(self, message: str, message_lower: str) -> Dict[str, str]:
        """
        Extrait les paramètres pour l'estimation du temps de trajet.
        Utilise 6 variantes de patterns pour capturer origin_name et destination_name.
        """
        params = {}
        
        # Déterminer si "ma position" est mentionnée
        has_my_position = any(phrase in message_lower for phrase in [
            'ma position', 'position actuelle', 'où je suis', 'ici', 'd\'ici', 'depuis d\'ici'
        ])
        
        # Variante 1: Pattern "de X à Y" - split par "à" d'abord
        if ' à ' in message_lower or ' a ' in message_lower:
            parts = re.split(r'\s+(?:à|a)\s+', message_lower, maxsplit=1)
            if len(parts) == 2:
                before_a, after_a = parts
                
                # Chercher "de X" à la FIN de "before_a"
                de_patterns = [
                    r'(?:^|\s)de\s+l\'([a-zéèêàâôù][\w\'\-0-9]{2,}?)\s*$',
                    r'(?:^|\s)de\s+(?:la|le|les|une|un|des)\s+([a-zéèêàâôù][\w\'\-0-9]{2,}?)\s*$',
                    r'(?:^|\s)de\s+([a-zA-Z][a-zéèêàâôù\-0-9]{2,}?)\s*$',
                ]
                
                origin = None
                for pattern in de_patterns:
                    m = re.search(pattern, before_a)
                    if m:
                        origin = m.group(1).strip()
                        break
                
                # Extraire destination
                if origin:
                    dest_patterns = [
                        r'^l\'([a-zéèêàâôù][\w\s\'\-0-9]{2,})',
                        r'^(?:la|le|les|une|un|des)\s+([a-zéèêàâôù][\w\s\'\-0-9]{2,})',
                        r'^([a-zA-Z][a-zéèêàâôù\s\'\-0-9]{2,})',
                    ]
                    
                    dest = None
                    for pattern in dest_patterns:
                        m = re.match(pattern, after_a)
                        if m:
                            dest = m.group(1).strip()
                            break
                    
                    if dest:
                        params['origin_name'] = origin
                        params['destination_name'] = dest
        
        # Variante 2: "entre X et Y"
        if 'origin_name' not in params:
            pattern_entre = r'entre\s+([a-zÀ-ÿA-Z][\w\s\'\-]+?)\s+et\s+(?:la|le|les|l\'|une|un|des)?\s*([a-zÀ-ÿA-Z][\w\s\'\-]+?)(?:\s*[\?!.]|$)'
            m = re.search(pattern_entre, message, re.IGNORECASE)
            if m:
                origin = m.group(1).strip()
                if origin.lower() in ['ma position', 'position actuelle', 'où je suis', 'ici']:
                    params['origin_name'] = 'ma position'
                else:
                    params['origin_name'] = origin
                params['destination_name'] = m.group(2).strip()
        
        # Variante 3: "aller à X en partant de ma position"
        if 'origin_name' not in params and has_my_position:
            pattern_en_partant = r'aller\s+(?:à|a|vers|au)\s+(?:la|le|les|l\'|une|un|des)?\s*(.+?)\s+en\s+partant'
            m = re.search(pattern_en_partant, message, re.IGNORECASE)
            if m:
                dest = m.group(1).strip()
                params['origin_name'] = 'ma position'
                params['destination_name'] = dest
        
        # Variante 4: "aller à X depuis ma position"
        if 'origin_name' not in params and has_my_position:
            pattern_depuis = r'aller\s+(?:à|a|vers|au)\s+(?:la|le|les|l\'|une|un|des)?\s*(.+?)\s+depuis'
            m = re.search(pattern_depuis, message, re.IGNORECASE)
            if m:
                dest = m.group(1).strip()
                params['origin_name'] = 'ma position'
                params['destination_name'] = dest
        
        # Variante 5: Simple "aller à X"
        if 'destination_name' not in params:
            pattern_aller = r'(?:combien de temps|temps|duree|pour)?\s*(?:aller|se rendre|me rendre)\s+(?:à|a|vers|au)\s+(?:la|le|les|l\'|une|un|des)?\s*([a-zéèêàâôùA-ZÀ-ÿ][\w\s\'\-]{2,})(?:\s*[\?!.]|$)'
            m = re.search(pattern_aller, message, re.IGNORECASE)
            if m:
                dest = m.group(1).strip()
                # Nettoyer les artifacts
                for word in ['en', 'pour', 'depuis', 'd\'']:
                    if ' ' + word in dest.lower():
                        dest = dest.split(word, 1)[0].strip()
                params['destination_name'] = dest
                # Si pas d'origine spécifiée, utiliser "ma position" par défaut
                if 'origin_name' not in params:
                    params['origin_name'] = 'ma position'
        
        # Variante 6: Fallback - chercher 2 mots en majuscule
        if 'origin_name' not in params and 'destination_name' not in params:
            excluded_words = [
                'combien', 'pourquoi', 'comment', 'quand', 'où', 'quel', 'quelle', 'quels', 'quelles',
                'qu\'est', 'est-ce', 'c\'est', 'y', 'a', 'la', 'le', 'les', 'un', 'une', 'des'
            ]
            
            pattern_caps = r'\b([A-ZÀ-ÿ][\w\s]*?)\b.*?\b([A-ZÀ-ÿ][\w\s]*?)\b'
            matches = re.findall(pattern_caps, message)
            if len(matches) >= 2:
                if isinstance(matches[0], tuple):
                    word1 = matches[0][0].strip().lower()
                    word2 = matches[0][1].strip().lower()
                    
                    if word1 not in excluded_words:
                        params['origin_name'] = matches[0][0].strip()
                    
                    if word2 not in excluded_words:
                        params['destination_name'] = matches[0][1].strip()
                else:
                    word1 = matches[0].strip().lower()
                    if word1 not in excluded_words:
                        params['origin_name'] = matches[0].strip()
                    
                    if len(matches) > 1:
                        word2 = matches[1].strip().lower()
                        if word2 not in excluded_words:
                            params['destination_name'] = matches[1].strip()
        
        return params
    
    def _extract_result_limit(self, message_lower: str) -> Dict[str, int]:
        """Extrait la limite de résultats."""
        if any(word in message_lower for word in ['top 3', '3 premiers', 'trois']):
            return {'limit': 3}
        elif any(word in message_lower for word in ['top 5', '5 premiers', 'cinq']):
            return {'limit': 5}
        else:
            return {'limit': 5}
