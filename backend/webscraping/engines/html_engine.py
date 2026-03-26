"""
HTML Scraper Engine
Uses requests + BeautifulSoup for static HTML scraping
"""
import requests
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import time
import random
import logging

from .base_engine import BaseScraperEngine, ScrapedItem
from ..processors.selector_processor import SelectorProcessor
from ..processors.date_parser import DateParser

logger = logging.getLogger(__name__)

# Pool of realistic browser User-Agents for rotation
USER_AGENT_POOL = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
]

class HTMLScraperEngine(BaseScraperEngine):
    """
    HTML scraping engine using requests + BeautifulSoup + Cloudscraper
    Best for: Static HTML pages without JavaScript, bypasses basic bot protection
    """
    
    def setup(self):
        """Setup HTTP session with cloudscraper and human-like headers"""
        # Replace requests.Session with cloudscraper to bypass anti-bot
        if HAS_CLOUDSCRAPER:
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
        else:
            self.session = requests.Session()

        # Rotate User-Agent randomly
        self._current_ua = random.choice(USER_AGENT_POOL)

        self.session.headers.update({
            'User-Agent': self._current_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })

        # Custom headers override
        if self.config.custom_headers:
            self.session.headers.update(self.config.custom_headers)

        # Cookies
        if self.config.cookies:
            for name, value in self.config.cookies.items():
                self.session.cookies.set(name, value)

        # Initialize processors
        self.selector_processor = SelectorProcessor(self.config.selector_type)
        self.date_parser = DateParser(self.config.date_format)

        logger.info(f"HTML engine setup for {self.config.name} | UA: {self._current_ua[:60]}...")
    
    def cleanup(self):
        """Close session"""
        if hasattr(self, 'session'):
            self.session.close()
        logger.info("HTML engine cleanup complete")
    
    def login(self) -> bool:
        """
        Handle form-based login
        """
        if not self.config.requires_login:
            return True
        
        try:
            logger.info(f"Attempting login to {self.config.login_url}")
            
            # Get login page
            login_page = self.session.get(
                self.config.login_url,
                timeout=self.config.timeout_seconds
            )
            login_page.raise_for_status()
            
            soup = BeautifulSoup(login_page.content, 'lxml')
            
            # Find login form
            form = soup.find('form')
            if not form:
                logger.error("Login form not found")
                return False
            
            # Build form data
            form_data = {}
            
            # Get all input fields
            for input_field in form.find_all('input'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    form_data[name] = value
            
            # Set credentials
            form_data[self.config.login_username_field] = self.config.username
            form_data[self.config.login_password_field] = self.config.password
            
            # Get form action
            action = form.get('action', '')
            if action:
                login_url = urljoin(self.config.login_url, action)
            else:
                login_url = self.config.login_url
            
            # Submit login
            response = self.session.post(
                login_url,
                data=form_data,
                timeout=self.config.timeout_seconds,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check if login successful
            # (You can add custom success check logic here)
            if 'logout' in response.text.lower() or 'sign out' in response.text.lower():
                logger.info("Login successful")
                return True
            
            logger.warning("Login may have failed (no logout link found)")
            return True  # Proceed anyway
            
        except Exception as e:
            logger.error(f"Login failed: {e}", exc_info=True)
            return False
    
    def navigate_to_page(self, url: str) -> BeautifulSoup:
        """
        Navigate to URL with human-like timing and retry logic.
        Retries up to 3 times with exponential backoff on failure.
        """
        max_retries = getattr(self.config, 'max_retries', 3)

        for attempt in range(1, max_retries + 1):
            try:
                # Human-like random delay (1.5s – 4.5s)
                delay = random.uniform(1.5, 4.5)
                time.sleep(delay)

                # Rotate Referer header to simulate user browsing flow
                self.session.headers.update({
                    'Referer': self.config.base_url,
                    'User-Agent': random.choice(USER_AGENT_POOL),
                })

                response = self.session.get(
                    url,
                    timeout=self.config.timeout_seconds,
                    verify=getattr(self.config, 'verify_ssl', True),
                    allow_redirects=True,
                )
                response.raise_for_status()  # raises HTTPError on 4xx/5xx

                self.requests_made += 1
                self.bytes_downloaded += len(response.content)

                soup = BeautifulSoup(response.content, 'lxml')
                logger.info(f"[{self.config.name}] Fetched {url} in attempt {attempt} ({delay:.1f}s delay)")
                return soup

            except requests.HTTPError as e:
                logger.warning(f"[{self.config.name}] HTTP {e.response.status_code} on {url} (attempt {attempt})")
                if e.response.status_code in (403, 404, 410, 451):
                    # Don't retry permanent errors
                    self.failed_urls.append(url)
                    raise
                if attempt < max_retries:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    logger.info(f"Retrying in {backoff:.1f}s...")
                    time.sleep(backoff)

            except requests.RequestException as e:
                logger.warning(f"[{self.config.name}] Network error on {url} (attempt {attempt}): {e}")
                if attempt < max_retries:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    time.sleep(backoff)

        self.failed_urls.append(url)
        raise requests.RequestException(f"Failed to fetch {url} after {max_retries} attempts")
    
    def extract_items(self, page_content: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract items from page using configured selectors
        """
        items = []
        selectors = self.config.selectors or {}
        
        # Get item container selector (supporting aliases)
        container_selector = selectors.get('item_container') or selectors.get('container') or 'article'
        
        # Find all item containers
        item_elements = self.selector_processor.select_multiple(
            page_content,
            container_selector
        )
        
        logger.info(f"Found {len(item_elements)} items on page")
        
        for item_elem in item_elements:
            try:
                item_data = {}
                
                # Extract each field
                for field_name, field_config in selectors.items():
                    if field_name in ('item_container', 'pagination_next', 'pagination_pages'):
                        continue
                    
                    # Handle Sibling Row Logic (e.g. WikiCfp 2-row table)
                    current_el = item_elem
                    target_config = field_config
                    
                    if self.config.use_sibling_payload and isinstance(field_config, str) and field_config.startswith('+'):
                        # Look at the next sibling (usually the next <tr>)
                        current_el = item_elem.find_next_sibling()
                        target_config = field_config[1:] # Remove the '+'
                    elif self.config.use_sibling_payload and isinstance(field_config, dict) and field_config.get('selector', '').startswith('+'):
                        current_el = item_elem.find_next_sibling()
                        target_config = field_config.copy()
                        target_config['selector'] = target_config['selector'][1:]

                    if not current_el:
                        logger.debug(f"Sibling element not found for field {field_name}")
                        continue

                    # Extract field value
                    value = self._extract_field(current_el, target_config, field_name)
                    item_data[field_name] = value
                
                items.append(item_data)
                
            except Exception as e:
                logger.error(f"Item extraction error: {e}", exc_info=True)
                continue
        
        return items
    
    def _extract_field(self, element: BeautifulSoup, field_config: Any, field_name: str = '') -> Any:
        """
        Extract single field from element
        
        Args:
            element: BeautifulSoup element
            field_config: Can be:
                - String: simple selector
                - Dict: {"selector": "...", "attr": "text|href|...", "multiple": true/false}
            field_name: Name of the field being extracted (for special handling)
        """
        # Handle simple string selector
        if isinstance(field_config, str):
            # For URL fields, default to href attribute instead of text
            default_attr = 'text'
            if field_name in ('url', 'source_url'):
                default_attr = 'href'
            elif field_name in ('image_url', 'image'):
                default_attr = 'src'
            elif field_name == 'pdf_url':
                default_attr = 'href'
            field_config = {"selector": field_config, "attr": default_attr}
        
        if not isinstance(field_config, dict):
            return None
        
        selector = field_config.get('selector', '')
        attr = field_config.get('attr', 'text')
        multiple = field_config.get('multiple', False)
        
        if not selector:
            return None
        
        # Extract value(s)
        if multiple:
            elements = self.selector_processor.select_multiple(element, selector)
            values = []
            for elem in elements:
                value = self.selector_processor.get_attribute(elem, attr)
                if value:
                    values.append(value)
            return values
        else:
            elem = self.selector_processor.select_one(element, selector)
            if elem:
                # For images: check lazy-load attributes before src
                if attr in ('src', 'image'):
                    for img_attr in ('data-src', 'data-lazy-src', 'data-original', 'src'):
                        val = self.selector_processor.get_attribute(elem, img_attr)
                        if val:
                            return self._normalize_url(val)
                return self.selector_processor.get_attribute(elem, attr)
            return None
    
    def get_next_page_url(self, page_content: BeautifulSoup, current_page: int) -> Optional[str]:
        """
        Get next page URL based on pagination strategy.
        Returns None to stop pagination.
        """
        if self.config.pagination_type == 'none':
            return None

        elif self.config.pagination_type in ('url_pattern', 'url_increment'):
            # URL_INCREMENT: use pagination_template (mandatory, explicit)
            # url_pattern: use pagination_url_pattern (legacy)
            template = (
                getattr(self.config, 'pagination_template', '') or
                getattr(self.config, 'pagination_url_pattern', '')
            )
            if template:
                next_page = current_page + 1
                return template.replace('{page}', str(next_page))
            return None

        elif self.config.pagination_type == 'next_button':
            # Find next button
            selectors = self.config.selectors or {}
            next_selector = selectors.get('pagination_next', 'a.next, [rel="next"]')
            next_elem = self.selector_processor.select_one(page_content, next_selector)
            if next_elem:
                href = self.selector_processor.get_attribute(next_elem, 'href')
                if href:
                    return self._normalize_url(href)
            return None

        elif self.config.pagination_type == 'page_numbers':
            selectors = self.config.selectors or {}
            page_selector = selectors.get('pagination_pages', '.pagination a')
            page_elements = self.selector_processor.select_multiple(page_content, page_selector)
            for elem in page_elements:
                text = self.selector_processor.get_attribute(elem, 'text')
                if text and text.strip().isdigit():
                    page_num = int(text.strip())
                    if page_num == current_page + 1:
                        href = self.selector_processor.get_attribute(elem, 'href')
                        if href:
                            return self._normalize_url(href)
            return None

        return None

    def _normalize_url(self, url: str) -> str:
        """
        Convert a relative URL to absolute using the scraper's base_url.
        Handles both path-relative and protocol-relative URLs.

        Examples:
            /haber/foo  -> https://www.ankara.edu.tr/haber/foo
            //cdn.com/x -> https://cdn.com/x
            https://... -> unchanged
        """
        if not url:
            return url
        return urljoin(self.config.base_url, url)
    
    def _normalize_item(self, raw_item: Dict[str, Any]) -> ScrapedItem:
        """
        Normalize raw extracted item to ScrapedItem format.
        Includes URL normalization (relative → absolute).
        """
        # Parse authors
        authors = []
        authors_data = raw_item.get('authors', [])
        if isinstance(authors_data, list):
            for author in authors_data:
                if isinstance(author, str):
                    authors.append({'name': author})
                elif isinstance(author, dict):
                    authors.append(author)
        elif isinstance(authors_data, str):
            for name in authors_data.split(','):
                if name.strip():
                    authors.append({'name': name.strip()})

        # Field aliases (Step 7: Robustness)
        title = raw_item.get('title') or raw_item.get('name', '')
        abstract = raw_item.get('abstract') or raw_item.get('description') or raw_item.get('summary', '')
        raw_date = raw_item.get('published_date') or raw_item.get('date')
        raw_url = raw_item.get('url') or raw_item.get('link', '')
        raw_pdf = raw_item.get('pdf_url') or raw_item.get('pdf', '')
        raw_image = raw_item.get('image_url') or raw_item.get('image') or raw_item.get('img', '')

        # Parse date
        pub_date = None
        if raw_date:
            pub_date = self.date_parser.parse(raw_date)

        # Parse categories
        categories = []
        cats_data = raw_item.get('categories') or raw_item.get('tags', [])
        if isinstance(cats_data, list):
            categories = [str(c) for c in cats_data]
        elif isinstance(cats_data, str):
            categories = [c.strip() for c in cats_data.split(',') if c.strip()]

        # --- URL Normalization (Step 6) ---
        normalized_url = self._normalize_url(raw_url) if raw_url else ''
        normalized_pdf = self._normalize_url(raw_pdf) if raw_pdf else ''
        normalized_image = self._normalize_url(raw_image) if raw_image else ''

        # Generate external ID (from normalized URL so duplicates are caught)
        external_id = raw_item.get('external_id') or self._generate_external_id(
            normalized_url or title
        )

        return ScrapedItem(
            title=title,
            url=normalized_url,
            external_id=external_id,
            abstract=abstract,
            authors=authors,
            published_date=pub_date,
            source_name=self.config.name,
            categories=categories,
            keywords=raw_item.get('keywords', []),
            content_type=raw_item.get('content_type', 'article'),
            journal=raw_item.get('journal', ''),
            doi=raw_item.get('doi', ''),
            pdf_url=normalized_pdf,
            image_url=normalized_image,
            location=raw_item.get('location', ''),
            event_date=raw_item.get('event_date'),
            deadline=raw_item.get('deadline'),
            amount=raw_item.get('amount', ''),
            raw_data={
                'source': self.config.name,
                'engine': 'html',
                'original_data': raw_item
            }
        )
