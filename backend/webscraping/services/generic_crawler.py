import logging
import urllib.parse
from typing import List, Dict, Any, Set
from django.utils import timezone
from .scraper_orchestrator import ScraperOrchestrator

logger = logging.getLogger(__name__)

class GenericCrawlerService:
    """
    Generic Multi-Stage Crawler Service.
    Driven entirely by ScraperConfig.
    
    Stages:
    1. Discovery (Step 1): Uses step1_selectors to find URLs to visit next.
    2. Extraction (Step 2): Visits discovered URLs and uses step2_selectors for final data.
    """
    
    def __init__(self, config):
        self.config = config
        self.orchestrator = ScraperOrchestrator(config)
        self.visited_urls: Set[str] = set()
        
    def crawl(self, query: str = None, test_mode: bool = False) -> Dict[str, Any]:
        """
        Execute the multi-stage crawling process.
        """
        logger.info(f"Starting Generic Multi-Stage Crawl for: {self.config.name}")
        
        # Track statistics
        stats = {
            'urls_discovered': 0,
            'pages_visited': 0,
            'items_extracted': 0,
            'errors': []
        }
        
        all_items = []
        
        try:
            # Stage 1: Discovery
            # We use the base_url as the starting point for discovery
            discovery_url = self._prepare_initial_url(query)
            logger.info(f"Stage 1: Discovering links from {discovery_url}")
            
            # Step 1 logic: extract URLs from the master page
            discovered_links = self._discover_urls(discovery_url, query)
            stats['urls_discovered'] = len(discovered_links)
            stats['pages_visited'] += 1
            
            logger.info(f"Stage 1: Found {len(discovered_links)} links to visit.")
            
            # Stage 2: Extraction
            # Iterate through discovered URLs and extract final data
            for i, link in enumerate(discovered_links):
                if stats['pages_visited'] >= self.config.max_pages_per_step:
                    logger.warning(f"Max pages limit ({self.config.max_pages_per_step}) reached. Stopping.")
                    break
                    
                if link in self.visited_urls:
                    continue
                
                logger.info(f"Stage 2 [{i+1}/{len(discovered_links)}]: Extracting from {link}")
                
                # Perform extraction on the sub-page
                # We use use_step1_selectors=False (implicitly uses standard 'selectors' or 'step2_selectors')
                result = self.orchestrator.scrape(
                    url_override=link,
                    test_mode=test_mode,
                    use_step2_selectors=True, # Custom flag we'll add to orchestrator
                    triggered_by='crawler'
                )
                
                self.visited_urls.add(link)
                stats['pages_visited'] += 1
                
                if result.get('success'):
                    extracted_items = result.get('items', [])
                    all_items.extend(extracted_items)
                    stats['items_extracted'] += len(extracted_items)
                else:
                    error_msg = result.get('error', 'Unknown Error')
                    stats['errors'].append({'url': link, 'error': error_msg})
                    logger.error(f"Error on {link}: {error_msg}")

            logger.info(f"Crawl finished. Total items: {stats['items_extracted']}")
            
            return {
                'success': True,
                'items': all_items,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Generic Crawler failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'stats': stats
            }

    def _prepare_initial_url(self, query: str) -> str:
        """Apply query encoding if enabled"""
        url = self.config.base_url
        if query and self.config.enable_query_encoding:
            # Basic query append/replace logic
            encoded_query = urllib.parse.quote(query)
            if '{query}' in url:
                url = url.replace('{query}', encoded_query)
            elif '?' in url:
                url += f"&q={encoded_query}"
            else:
                url += f"?q={encoded_query}"
        return url

    def _discover_urls(self, url: str, query: str) -> List[str]:
        """Use Step 1 selectors to find URLs"""
        # We tell the orchestrator to use Step 1 selectors only
        result = self.orchestrator.scrape(
            url_override=url,
            test_mode=True, # We only need raw results for discovery
            use_step1_selectors=True,
            triggered_by='crawler_discovery'
        )
        
        if not result.get('success'):
            logger.error(f"Discovery failed on {url}: {result.get('error')}")
            return []
            
        raw_items = result.get('items', [])
        links = []
        
        for item in raw_items:
            # We look for 'url' or 'link' in extracted fields
            # The user configures step1_selectors to return at least one URL field
            link = None
            if isinstance(item, dict):
                link = item.get('url') or item.get('link') or item.get('source_url')
            elif hasattr(item, 'url'):
                link = item.url
                
            if link:
                # Relative URL fix if enabled
                if self.config.enable_relative_url_fix:
                    link = urllib.parse.urljoin(url, link)
                links.append(link)
                
        # Deduplicate
        return list(dict.fromkeys(links))
