import logging
import urllib.parse
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from .scraper_orchestrator import ScraperOrchestrator

logger = logging.getLogger(__name__)

class WikiCFPCrawlerService:
    """
    Specialized crawler for WikiCFP (http://www.wikicfp.com)
    Implements a 4-stage pipeline:
    1. Category Discovery
    2. URL Generation (Encoded)
    3. Pagination Handling
    4. Structured Data Extraction
    """
    
    BASE_MASTER_URL = "http://www.wikicfp.com/cfp/allcat"
    CATEGORY_URL_TEMPLATE = "http://www.wikicfp.com/cfp/call?conference={category}&page={page}"

    def __init__(self, config=None):
        self.config = config
        self.orchestrator = ScraperOrchestrator(config) if config else None

    def crawl(self, test_mode: bool = False, limit_categories: int = 2) -> Dict[str, Any]:
        """
        Runs the full multi-stage crawling pipeline.
        
        Args:
            test_mode: If True, does not save to DB and returns sample data.
            limit_categories: Limit number of categories for safety/speed during tests.
        """
        logger.info("Starting WikiCFP Multi-Stage Crawl...")
        
        # STAGE 1: Category Discovery
        categories = self._discover_categories()
        logger.info(f"Stage 1: Discovered {len(categories)} categories.")
        
        if limit_categories:
            categories = categories[:limit_categories]
            logger.info(f"Limiting to first {limit_categories} categories for this run.")

        all_results = []
        total_items = 0
        
        # STAGE 2 & 3: Iterate through categories and pagination
        for cat_name, cat_slug in categories:
            logger.info(f"Stage 2/3: Crawling Category: {cat_name}")
            cat_items = self._crawl_category(cat_name, test_mode)
            all_results.extend(cat_items)
            total_items += len(cat_items)
            
        logger.info(f"Crawl completed. Total items found: {total_items}")
        
        return {
            "success": True,
            "total_categories": len(categories),
            "total_items": total_items,
            "items": all_results[:20] if test_mode else [] # Return samples if test
        }

    def _discover_categories(self) -> List[tuple]:
        """Stage 1: Scraping category list"""
        try:
            response = requests.get(self.BASE_MASTER_URL, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Categories are usually in tables, inside <a> tags with /cfp/call?conference=
            category_links = []
            for a in soup.select('a[href*="/cfp/call?conference="]'):
                name = a.get_text(strip=True)
                # Extract slug from href
                href = a.get('href', '')
                slug = href.split('conference=')[-1]
                if name and slug:
                    category_links.append((name, slug))
            
            return category_links
        except Exception as e:
            logger.error(f"Category discovery failed: {e}")
            return []

    def _crawl_category(self, category_name: str, test_mode: bool = False) -> List[Dict]:
        """Stage 3 & 4: Pagination and Extraction for a single category"""
        page = 1
        category_items = []
        
        # URL Encoded category
        encoded_cat = urllib.parse.quote(category_name)
        
        while True:
            url = self.CATEGORY_URL_TEMPLATE.format(category=encoded_cat, page=page)
            logger.info(f"Scraping {category_name} - Page {page}: {url}")
            
            # Setup specialized config if not provided, or override URL
            if not self.orchestrator:
                # Fallback for standalone usage
                logger.warning("No config provided, using default WikiCFP settings")
                # In a real app, we'd fetch a 'WikiCFP' config from DB
                return [] 

            # Temporarily modify orchestrator's config for this specific page
            # We use test_mode=True internally to get items back for our local accumulation
            # unless we want the orchestrator to save them directly.
            result = self.orchestrator.scrape(
                url_override=url,
                test_mode=test_mode,
                triggered_by='crawler'
            )
            
            if not result.get('success'):
                logger.error(f"Failed to scrape page {page} for {category_name}: {result.get('error')}")
                break
                
            items = result.get('items', [])
            if not items:
                logger.info(f"No more items found for {category_name} at page {page}. Stopping.")
                break
            
            # Tag items with category
            for item in items:
                if isinstance(item, dict):
                    item['category'] = category_name
                else:
                    item.category = category_name # If it's a ScrapedItem object
            
            category_items.extend(items)
            
            # Safety break
            if page >= 10: # Max 10 pages per category for safety
                break
                
            page += 1
            
        return category_items
