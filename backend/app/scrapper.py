# backend/app/scrapper.py
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

def scrape_url(url: str) -> dict:
    """
    Scrape une URL et retourne titre, texte, liens
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraction
        title = soup.find('title').text if soup.find('title') else 'Pas de titre'
        
        # Extraire les paragraphes
        paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text.strip()]
        
        # Extraire les liens
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http'):
                links.append(href)
        
        return {
            "success": True,
            "title": title,
            "content": " ".join(paragraphs)[:5000],  # Limiter à 5000 chars
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }