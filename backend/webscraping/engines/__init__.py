"""
Scraper Engines
"""
from .base_engine import BaseScraperEngine, ScrapedItem
from .html_engine import HTMLScraperEngine
from .factory import ScraperEngineFactory, load_selenium_engine, load_playwright_engine

# Lazy imports for optional engines
def get_selenium_engine():
    """Lazy import Selenium engine"""
    if load_selenium_engine():
        from .selenium_engine import SeleniumScraperEngine
        return SeleniumScraperEngine
    return None

def get_playwright_engine():
    """Lazy import Playwright engine"""
    if load_playwright_engine():
        from .playwright_engine import PlaywrightScraperEngine
        return PlaywrightScraperEngine
    return None

__all__ = [
    'BaseScraperEngine',
    'ScrapedItem',
    'HTMLScraperEngine',
    'ScraperEngineFactory',
    'load_selenium_engine',
    'load_playwright_engine',
    'get_selenium_engine',
    'get_playwright_engine',
]
