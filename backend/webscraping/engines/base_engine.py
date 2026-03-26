"""
Base Scraper Engine - Abstract Base Class
All scraper engines must inherit from this
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import date
import logging
import requests

logger = logging.getLogger(__name__)


@dataclass
class ScrapedItem:
    """
    Normalized scraped item structure
    Standard format for all scrapers
    """
    title: str
    url: str
    external_id: str
    abstract: str = ""
    authors: List[Dict[str, str]] = field(default_factory=list)
    published_date: Optional[date] = None
    source_name: str = ""
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    content_type: str = "article"
    journal: str = ""
    doi: str = ""
    pdf_url: str = ""
    image_url: str = ""
    location: str = ""  # For conferences
    event_date: Optional[date] = None  # For events
    deadline: Optional[date] = None  # For funding
    amount: str = ""  # For funding
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate required fields"""
        if not self.title or len(self.title.strip()) < 3:
            logger.warning(f"Invalid title: {self.title}")
            return False
        if not self.external_id:
            logger.warning("Missing external_id")
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'title': self.title,
            'source_url': self.url,
            'external_id': self.external_id,
            'abstract': self.abstract,
            'authors': self.authors,
            'published_date': self.published_date,
            'categories': self.categories,
            'keywords': self.keywords,
            'content_type': self.content_type,
            'journal': self.journal,
            'doi': self.doi,
            'pdf_url': self.pdf_url,
            'image_url': self.image_url,
            'location': self.location,
            'event_date': self.event_date,
            'deadline': self.deadline,
            'amount': self.amount,
            'raw_data': self.raw_data
        }


class BaseScraperEngine(ABC):
    """
    Abstract base class for all scraper engines
    
    Responsibilities:
    - Setup session/browser
    - Handle login
    - Navigate pages
    - Extract data using selectors
    - Handle pagination
    - Cleanup resources
    """
    
    def __init__(self, config):
        """
        Args:
            config: ScraperConfig model instance
        """
        self.config = config
        self.items_scraped = []
        self.pages_scraped = 0
        self.requests_made = 0
        self.bytes_downloaded = 0
        self.failed_urls = []
    
    @abstractmethod
    def setup(self):
        """
        Setup scraping environment
        - Initialize session/browser
        - Set headers
        - Configure options
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Cleanup resources
        - Close browser
        - Close session
        """
        pass
    
    @abstractmethod
    def login(self) -> bool:
        """
        Handle authentication if required
        
        Returns:
            True if login successful or not required
            False if login failed
        """
        pass
    
    @abstractmethod
    def navigate_to_page(self, url: str) -> Any:
        """
        Navigate to URL and return page content
        
        Args:
            url: Target URL
            
        Returns:
            Page content (HTML string, BeautifulSoup, or WebDriver)
        """
        pass
    
    @abstractmethod
    def extract_items(self, page_content: Any) -> List[Dict[str, Any]]:
        """
        Extract items from page using selectors
        
        Args:
            page_content: Page content from navigate_to_page
            
        Returns:
            List of raw extracted items
        """
        pass
    
    @abstractmethod
    def get_next_page_url(self, page_content: Any, current_page: int) -> Optional[str]:
        """
        Get next page URL for pagination
        
        Args:
            page_content: Current page content
            current_page: Current page number
            
        Returns:
            Next page URL or None if no more pages
        """
        pass
    
    def scrape(self, query: str = None, max_results: int = None) -> List[ScrapedItem]:
        """
        Main scraping method - orchestrates entire pagination loop.

        Handles:
        - URL_INCREMENT pagination (template with {page})
        - stop_when_empty: stops when a page yields no items
        - HTTP error handling: stops on non-200 or network failure
        - Duplicate detection: delegated to save layer (unique_together)
        """
        try:
            self.setup()
            
            # Check for graceful degradation (e.g. Playwright not installed)
            if hasattr(self, 'available') and not self.available:
                logger.warning(f"[{self.config.name}] Engine unavailable. Returning 0 items.")
                return []

            if self.config.requires_login:
                if not self.login():
                    raise Exception("Login failed")

            search_query = query or getattr(self.config, 'search_query', '')
            self.query = search_query
            result_limit = max_results or self.config.max_results

            # --- Determine starting page and URL ---
            current_page = getattr(self.config, 'pagination_start_page', 1)
            stop_when_empty = getattr(self.config, 'stop_when_empty', True)
            pagination_type = getattr(self.config, 'pagination_type', 'none')

            # For url_increment: build first URL from the template
            if pagination_type == 'url_increment':
                template = (
                    getattr(self.config, 'pagination_template', '') or
                    getattr(self.config, 'pagination_url_pattern', '')
                )
                if not template:
                    raise ValueError(
                        "url_increment pagination requires 'pagination_template' to be set. "
                        "Example: https://www.site.com/haberler/{page}"
                    )
                current_url = template.replace('{page}', str(current_page))
            else:
                current_url = self._build_start_url(search_query, current_page)

            logger.info(
                f"[{self.config.name}] Starting scrape: type={pagination_type}, "
                f"start_page={current_page}, stop_when_empty={stop_when_empty}, "
                f"max_pages={self.config.max_pages}, url={current_url}"
            )

            # --- Pagination loop ---
            while (
                self.pages_scraped < self.config.max_pages and
                len(self.items_scraped) < result_limit
            ):
                try:
                    page_content = self.navigate_to_page(current_url)

                    if not page_content:
                        logger.warning(f"Empty page content for {current_url} — stopping.")
                        break

                    # Extract raw items from this page
                    raw_items = self.extract_items(page_content)
                    items_on_page = len(raw_items)

                    logger.info(
                        f"[{self.config.name}] Page {current_page}: "
                        f"found {items_on_page} items at {current_url}"
                    )

                    # --- stop_when_empty (Step 2, Step 8) ---
                    if items_on_page == 0 and stop_when_empty:
                        logger.info(
                            f"[{self.config.name}] No items found on page {current_page}. "
                            "stop_when_empty=True → stopping pagination."
                        )
                        break

                    # Normalize and validate each item
                    for raw_item in raw_items:
                        if len(self.items_scraped) >= result_limit:
                            break
                        try:
                            scraped_item = self._normalize_item(raw_item)
                            if scraped_item and scraped_item.validate():
                                if self._passes_date_filter(scraped_item):
                                    self.items_scraped.append(scraped_item)
                        except Exception as e:
                            logger.error(f"Item normalization error: {e}", exc_info=True)
                            continue

                    self.pages_scraped += 1

                    if len(self.items_scraped) >= result_limit:
                        break

                    # Get next page URL
                    next_url = self.get_next_page_url(page_content, current_page)

                    if not next_url:
                        logger.info(f"[{self.config.name}] No more pages after page {current_page}.")
                        break

                    current_url = next_url
                    current_page += 1

                    import time
                    time.sleep(getattr(self.config, 'delay_between_pages', 2.0))

                except requests.HTTPError as e:
                    logger.error(
                        f"[{self.config.name}] HTTP {e.response.status_code} on {current_url} — stopping."
                    )
                    self.failed_urls.append(current_url)
                    break
                except Exception as e:
                    logger.error(f"[{self.config.name}] Page error for {current_url}: {e}", exc_info=True)
                    self.failed_urls.append(current_url)
                    break

            logger.info(
                f"[{self.config.name}] Scrape complete: "
                f"{len(self.items_scraped)} items from {self.pages_scraped} pages."
            )
            return self.items_scraped

        finally:
            self.cleanup()
    
    def _build_start_url(self, query: str, page: int) -> str:
        """Build starting URL with query and page"""
        search_template = getattr(self.config, 'search_url_template', None)
        if search_template:
            # Use template
            url = search_template
            url = url.replace('{query}', query or '')
            url = url.replace('{page}', str(page))
            url = url.replace('{category}', getattr(self.config, 'categories', '') or '')
            return url
        else:
            # Use base URL
            return getattr(self.config, 'base_url', '')
    
    @abstractmethod
    def _normalize_item(self, raw_item: Dict[str, Any]) -> ScrapedItem:
        """
        Normalize raw extracted item to ScrapedItem format
        
        Args:
            raw_item: Raw extracted data
            
        Returns:
            ScrapedItem instance
        """
        pass
    
    def _passes_date_filter(self, item: ScrapedItem) -> bool:
        """Check if item passes date filters"""
        if not item.published_date:
            return True  # No date, allow it
        
        if self.config.date_filter_start and item.published_date < self.config.date_filter_start:
            return False
        
        if self.config.date_filter_end and item.published_date > self.config.date_filter_end:
            return False
        
        return True
    
    def _generate_external_id(self, source: str) -> str:
        """Generate unique external ID"""
        import hashlib
        hash_input = f"{self.config.name}:{source}"
        return f"{self.config.source_type}:{hashlib.md5(hash_input.encode()).hexdigest()[:16]}"
    
    def _normalize_url(self, url: str) -> str:
        """Convert relative URL to absolute using base_url"""
        if not url:
            return ""
        if url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
            return url
        
        from urllib.parse import urljoin
        return urljoin(self.config.base_url, url)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return {
            'items_scraped': len(self.items_scraped),
            'pages_scraped': self.pages_scraped,
            'requests_made': self.requests_made,
            'bytes_downloaded': self.bytes_downloaded,
            'failed_urls': self.failed_urls
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(config={self.config.name})>"
