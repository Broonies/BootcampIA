# backend/app/tools/__init__.py
from .fuel_scraper import FuelPriceScraper
from .scraper import scrape_url

__all__ = ['FuelPriceScraper', 'scrape_url']