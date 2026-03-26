"""
Scraper Engine Factory
Selects appropriate engine based on configuration
"""
from typing import Type
import logging

from .base_engine import BaseScraperEngine
from .html_engine import HTMLScraperEngine

logger = logging.getLogger(__name__)


class ScraperEngineFactory:
    """
    Factory for creating scraper engines
    """
    
    # Engine registry
    _engines = {
        'html': HTMLScraperEngine,
        'rss': HTMLScraperEngine,  # RSS uses HTML engine with XML parsing
    }
    
    # Track which optional engines are loaded
    _loaded_engines = set()
    
    @classmethod
    def register_engine(cls, engine_type: str, engine_class: Type[BaseScraperEngine]):
        """
        Register a new engine type
        
        Args:
            engine_type: Engine identifier
            engine_class: Engine class (must inherit from BaseScraperEngine)
        """
        if not issubclass(engine_class, BaseScraperEngine):
            raise ValueError(f"{engine_class} must inherit from BaseScraperEngine")
        
        cls._engines[engine_type] = engine_class
        logger.info(f"Registered engine: {engine_type} -> {engine_class.__name__}")
    
    @classmethod
    def create_engine(cls, config) -> BaseScraperEngine:
        """
        Create appropriate engine based on config
        
        Args:
            config: ScraperConfig instance
            
        Returns:
            ScraperEngine instance
        """
        engine_type = getattr(config, 'scraper_type', getattr(config, 'scraper_engine', 'html'))
        
        # User tip: redirect legacy selenium configs to modern playwright
        if engine_type == 'selenium':
            engine_type = 'playwright'
        
        if engine_type not in cls._engines:
            logger.warning(f"Unknown engine type '{engine_type}', falling back to HTML engine")
            engine_type = 'html'
        
        engine_class = cls._engines[engine_type]
        
        logger.info(f"Creating {engine_class.__name__} for {config.name}")
        
        return engine_class(config)
    
    @classmethod
    def get_available_engines(cls) -> list:
        """Get list of available engine types"""
        return list(cls._engines.keys())


# Optional: Lazy loading for Selenium/Playwright
def load_selenium_engine():
    """
    Lazy load Selenium engine
    Only imports when needed to avoid dependency issues
    """
    if 'selenium' in ScraperEngineFactory._loaded_engines:
        return True
    
    try:
        from .selenium_engine import SeleniumScraperEngine
        ScraperEngineFactory.register_engine('selenium', SeleniumScraperEngine)
        ScraperEngineFactory._loaded_engines.add('selenium')
        logger.info("✓ Selenium engine loaded successfully")
        return True
    except ImportError as e:
        logger.warning(f"Selenium not available: {e}")
        logger.info("Install with: pip install selenium webdriver-manager")
        return False


def load_playwright_engine():
    """
    Lazy load Playwright engine
    """
    if 'playwright' in ScraperEngineFactory._loaded_engines:
        return True
    
    try:
        from .playwright_engine import PlaywrightScraperEngine
        ScraperEngineFactory.register_engine('playwright', PlaywrightScraperEngine)
        ScraperEngineFactory._loaded_engines.add('playwright')
        logger.info("✓ Playwright engine loaded successfully")
        return True
    except ImportError as e:
        logger.warning(f"Playwright not available: {e}")
        logger.info("Install with: pip install playwright && playwright install chromium")
        return False


# Auto-load engines if available
try:
    load_selenium_engine()
except Exception as e:
    logger.debug(f"Could not auto-load Selenium: {e}")

try:
    load_playwright_engine()
except Exception as e:
    logger.debug(f"Could not auto-load Playwright: {e}")
