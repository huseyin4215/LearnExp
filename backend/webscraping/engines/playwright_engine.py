"""
Playwright Scraper Engine
Modern browser automation for JavaScript-rendered sites
"""
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import time
import logging

from .base_engine import BaseScraperEngine, ScrapedItem
from ..processors.selector_processor import SelectorProcessor
from ..processors.date_parser import DateParser

logger = logging.getLogger(__name__)


class PlaywrightScraperEngine(BaseScraperEngine):
    """
    Playwright scraping engine for modern JavaScript-rendered sites
    Best for: Modern SPAs, React/Vue/Angular apps, complex JS interactions
    
    Requirements:
        pip install playwright
        playwright install chromium
    
    Advantages over Selenium:
        - Faster
        - Better API
        - Auto-waits for elements
        - Network interception
        - Multiple browser contexts
    """
    
    def setup(self):
        """Setup Playwright browser"""
        self.available = False
        try:
            from playwright.sync_api import sync_playwright
            
            # Start Playwright
            self.playwright = sync_playwright().start()
            
            # Launch browser
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )
            
            # Create context (like an incognito session)
            context_options = {
                'user_agent': self.config.user_agent,
                'viewport': {'width': 1920, 'height': 1080},
                'ignore_https_errors': not self.config.verify_ssl,
            }
            
            # Add custom headers
            if self.config.custom_headers:
                context_options['extra_http_headers'] = self.config.custom_headers
            
            self.context = self.browser.new_context(**context_options)
            
            # Set default timeout
            self.context.set_default_timeout(self.config.timeout_seconds * 1000)
            
            # Create page
            self.page = self.context.new_page()
            
            # Initial wait/navigation settings
            self.wait_until = 'networkidle'
            self.extra_wait = 2
            
            # Initialize processors
            self.selector_processor = SelectorProcessor(self.config.selector_type)
            self.date_parser = DateParser(self.config.date_format)
            
            self.available = True
            
            # Ensure debug directory exists
            import os
            if not os.path.exists('debug_scrapers'):
                os.makedirs('debug_scrapers')
                
            logger.info(f"Playwright engine setup complete for {self.config.name}")
            
        except ImportError as e:
            logger.error(f"Playwright not installed: {e}")
            self.available = False
    
    def cleanup(self):
        """Close browser"""
        try:
            if hasattr(self, 'page'):
                self.page.close()
            if hasattr(self, 'context'):
                self.context.close()
            if hasattr(self, 'browser'):
                self.browser.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
            logger.info("Playwright browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def login(self) -> bool:
        """
        Handle form-based login with Playwright
        """
        if not self.config.requires_login:
            return True
        
        try:
            logger.info(f"Attempting login to {self.config.login_url}")
            
            # Navigate to login page
            self.page.goto(self.config.login_url, wait_until='networkidle')
            
            # Fill username
            username_selector = f'[name="{self.config.login_username_field}"]'
            self.page.fill(username_selector, self.config.username)
            
            # Fill password
            password_selector = f'[name="{self.config.login_password_field}"]'
            self.page.fill(password_selector, self.config.password)
            
            # Click submit
            submit_selector = self.config.login_submit_selector or 'button[type="submit"]'
            self.page.click(submit_selector)
            
            # Wait for navigation
            self.page.wait_for_load_state('networkidle')
            
            # Check if login successful
            current_url = self.page.url
            if 'login' not in current_url.lower():
                logger.info("Login successful")
                return True
            
            logger.warning("Login may have failed (still on login page)")
            return True  # Proceed anyway
            
        except Exception as e:
            logger.error(f"Login failed: {e}", exc_info=True)
            return False
    
    def navigate_to_page(self, url: str) -> Any:
        """
        Navigate to URL and return page content
        """
        try:
            # Delay before request
            time.sleep(self.config.delay_between_requests)
            
            print(f"ENGINE NAVIGATING TO: {url}")
            # Navigate using specified wait strategy
            response = self.page.goto(url, wait_until=self.wait_until, timeout=self.config.timeout_seconds * 1000)
            
            # Check response status
            if response and response.status >= 400:
                print(f"ERROR: HTTP {response.status} for {url}")
                logger.warning(f"HTTP {response.status} for {url}")
            
            # 1. Wait for content to load (Dynamic approach)
            # Default to networkidle, but prioritize wait_for_selector if provided
            wait_selector = (
                self.config.selectors.get('wait_for') or 
                self.config.selectors.get('item_container') or 
                self.config.selectors.get('container')
            )
            
            try:
                if wait_selector:
                    logger.info(f"Waiting for selector: {wait_selector}")
                    self.page.wait_for_selector(wait_selector, timeout=self.config.timeout_seconds * 1000)
                else:
                    self.page.wait_for_load_state('networkidle', timeout=self.config.timeout_seconds * 1000)
            except Exception as e:
                logger.warning(f"Wait timeout on {url}: {e}")
                # Save debug info on failure
                self._save_debug_state(f"timeout_{int(time.time())}")
            
            # 2. Additional delay for animations/API completion
            if self.extra_wait:
                time.sleep(self.extra_wait)
            
            # 3. Infinite Scroll / Standard Scroll
            if getattr(self.config, 'enable_infinite_scroll', False) or self.config.selectors.get('infinite_scroll'):
                self._scroll_infinite()
            elif self.config.selectors.get('scroll'):
                self._scroll_page()
            
            # Update statistics
            self.requests_made += 1
            
            # Return current page object instead of soup for native extraction
            return self.page
            
        except Exception as e:
            logger.error(f"Navigation error for {url}: {e}", exc_info=True)
            self.failed_urls.append(url)
            raise
    
    def _scroll_page(self):
        """Standard scroll to trigger lazy loading"""
        try:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            time.sleep(0.5)
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
        except Exception:
            pass

    def _scroll_infinite(self, max_scrolls: int = None, delay_ms: int = None):
        """Robust infinite scroll handler using config settings"""
        max_scrolls = max_scrolls or getattr(self.config, 'scroll_count', 10)
        delay_sec = (delay_ms or getattr(self.config, 'scroll_delay', 2000)) / 1000.0
        
        try:
            last_height = self.page.evaluate("document.body.scrollHeight")
            for i in range(max_scrolls):
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(delay_sec)
                new_height = self.page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                logger.info(f"Scrolled {i+1}/{max_scrolls} times")
        except Exception as e:
            logger.warning(f"Infinite scroll error: {e}")
    
    def extract_items(self, page_obj: Any) -> List[Dict[str, Any]]:
        """
        Extract items from Playwright Page object using native selectors.
        More robust for SPAs than BeautifulSoup.
        """
        items = []
        selectors = self.config.selectors or {}
        
        # Get item container selector (supporting aliases)
        container_selector = selectors.get('item_container') or selectors.get('container') or 'article'
        
        # Explicitly wait for container again to ensure it's still there
        try:
             self.page.wait_for_selector(container_selector, timeout=5000)
        except:
             pass

        # Find all item containers (NATIVE PLAYWRIGHT)
        item_elements = self.page.query_selector_all(container_selector)
        logger.info(f"Native Playwright found {len(item_elements)} items on page using '{container_selector}'")
        
        if not item_elements:
             # Debug: Save page on zero results
             self._save_debug_state(f"zero_items_{int(time.time())}")

        for item_elem in item_elements:
            try:
                item_data = {}
                
                # Extract each field
                for field_name, field_config in selectors.items():
                    if field_name in ['item_container', 'container', 'pagination_next', 'wait_for', 'infinite_scroll']:
                        continue
                    
                    # Sibling Row Logic
                    current_el = item_elem
                    target_config = field_config
                    
                    if self.config.use_sibling_payload and isinstance(field_config, str) and field_config.startswith('+'):
                        current_el = item_elem.evaluate_handle('el => el.nextElementSibling')
                        if current_el.as_element() is None:
                            logger.debug(f"Sibling row not found for {field_name}")
                            continue
                        current_el = current_el.as_element()
                        target_config = field_config[1:]
                    elif self.config.use_sibling_payload and isinstance(field_config, dict) and field_config.get('selector', '').startswith('+'):
                        current_el = item_elem.evaluate_handle('el => el.nextElementSibling')
                        if current_el.as_element() is None:
                            logger.debug(f"Sibling row not found for {field_name}")
                            continue
                        current_el = current_el.as_element()
                        target_config = field_config.copy()
                        target_config['selector'] = target_config['selector'][1:]

                    # Extract field value natively
                    value = self._extract_field_native(current_el, target_config, field_name)
                    item_data[field_name] = value
                
                items.append(item_data)
                
            except Exception as e:
                print(f"Extraction error: {e}")
                logger.debug(f"Item extraction error: {e}")
                continue
        
        print(f"TOTAL ITEMS EXTRACTED ON PAGE: {len(items)}")
        return items
    
    def _extract_field_native(self, element: Any, field_config: Any, field_name: str) -> Any:
        """Extract single field natively from Playwright ElementHandle"""
        # Default attribute mapping
        default_attr = 'text'
        if field_name in ('url', 'link', 'pdf_url'): default_attr = 'href'
        elif field_name in ('image', 'img', 'image_url'): default_attr = 'src'

        # Handle simplified string selector
        if isinstance(field_config, str):
            field_config = {"selector": field_config, "attr": default_attr}
        
        if not isinstance(field_config, dict):
            return None
        
        selector = field_config.get('selector', '')
        attr = field_config.get('attr', default_attr).lower()
        
        if not selector:
            # If no selector, try to extract from current container element
            elem = element
        else:
            elem = element.query_selector(selector)
            
        if not elem:
            return None
            
        # Extract based on attribute
        if attr == 'text':
            return elem.inner_text().strip()
        elif attr == 'html':
            return elem.inner_html().strip()
        else:
            return elem.get_attribute(attr)

    def _save_debug_state(self, prefix: str):
        """Saves screenshot and HTML for debugging"""
        try:
            import os
            debug_dir = 'debug_scrapers'
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            timestamp = int(time.time())
            # HTML
            with open(f"{debug_dir}/{prefix}_{timestamp}.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            # Screenshot
            self.page.screenshot(path=f"{debug_dir}/{prefix}_{timestamp}.png")
        except Exception as e:
            logger.error(f"Debug save failed: {e}")

    def get_next_page_url(self, page_obj: Any, current_page: int) -> Optional[str]:
        """Get next page URL based on pagination strategy"""
        if self.config.pagination_type == 'none':
            return None
        
        elif self.config.pagination_type in ('url_pattern', 'url_increment'):
            # Prefer 'pagination_template' to match HTML engine improvements
            template = (
                getattr(self.config, 'pagination_template', '') or 
                getattr(self.config, 'pagination_url_pattern', '')
            )
            if template:
                next_page = current_page + 1
                return template.replace('{page}', str(next_page))
            return None
        
        elif self.config.pagination_type == 'next_button':
            selectors = self.config.selectors or {}
            next_selector = selectors.get('pagination_next', 'a.next, [rel="next"]')
            
            next_elem = self.selector_processor.select_one(page_content, next_selector)
            if next_elem:
                href = self.selector_processor.get_attribute(next_elem, 'href')
                if href:
                    return urljoin(self.config.base_url, href)
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
                            return urljoin(self.config.base_url, href)
            return None
        
        return None
    
    def _normalize_item(self, raw_item: Dict[str, Any]) -> ScrapedItem:
        """Normalize raw extracted item with alias support and filtering"""
        # Parsing basic fields with aliases (Robustness)
        title = (raw_item.get('title') or raw_item.get('name', '')).strip()
        abstract = (raw_item.get('abstract') or raw_item.get('description') or raw_item.get('summary', '')).strip()
        raw_date = raw_item.get('published_date') or raw_item.get('date')
        raw_url = raw_item.get('url') or raw_item.get('link', '')
        raw_pdf = raw_item.get('pdf_url') or raw_item.get('pdf', '')
        raw_image = raw_item.get('image_url') or raw_item.get('image') or raw_item.get('img', '')

        # Filter: Search Query (Early Exit) - Checks Title and Abstract
        query_match = not self.query  # If no query, it's a match
        
        if self.query:
            q = self.query.lower()
            if q in title.lower() or q in abstract.lower():
                query_match = True
            
            # Author check will be added after parsing authors (below)

        # Parse authors
        authors = []
        authors_data = raw_item.get('authors') or raw_item.get('yazarlar', [])
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
        
        # Author check and final filter decision
        if self.query and not query_match:
            # Check authors as well
            authors_text = " ".join([a.get('name', '').lower() for a in authors])
            if self.query.lower() in authors_text:
                query_match = True
            
            if not query_match:
                logger.info(f"Skipping item '{title[:30]}...' - No match for '{self.query}' in Title/Abstract/Authors")
                return None
        
        # Parse date
        pub_date = None
        if raw_date:
            pub_date = self.date_parser.parse(raw_date)
            
            # Filter: Date Range (Early Exit)
            if self.config.date_filter_start and pub_date < self.config.date_filter_start:
                logger.info(f"Skipping item '{title[:30]}...' - Too old: {pub_date} < {self.config.date_filter_start}")
                return None
            if self.config.date_filter_end and pub_date > self.config.date_filter_end:
                logger.info(f"Skipping item '{title[:30]}...' - Too new: {pub_date} > {self.config.date_filter_end}")
                return None
        
        # Parse categories
        categories = []
        cats_data = raw_item.get('categories') or raw_item.get('tags', [])
        if isinstance(cats_data, list):
            categories = [str(c) for c in cats_data]
        elif isinstance(cats_data, str):
            categories = [c.strip() for c in cats_data.split(',') if c.strip()]
        
        # Absolute URLs
        url = self._normalize_url(raw_url) if raw_url else ''
        pdf_url = self._normalize_url(raw_pdf) if raw_pdf else ''
        image_url = self._normalize_url(raw_image) if raw_image else ''
        
        # Generate external ID
        external_id = raw_item.get('external_id') or self._generate_external_id(
            url or title
        )
        
        return ScrapedItem(
            title=title,
            url=url,
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
            pdf_url=pdf_url,
            image_url=image_url,
            location=raw_item.get('location', ''),
            event_date=raw_item.get('event_date'),
            deadline=raw_item.get('deadline'),
            amount=raw_item.get('amount', ''),
            raw_data={
                'source': self.config.name,
                'engine': 'playwright',
                'original_data': raw_item
            }
        )
    
    def take_screenshot(self, filename: str = None):
        """Take screenshot (bonus feature)"""
        if not filename:
            import datetime
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            self.page.screenshot(path=filename, full_page=True)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
    
    def intercept_network(self, pattern: str, handler):
        """
        Intercept network requests (advanced feature)
        
        Example:
            def handle_api(route):
                print(f"API call: {route.request.url}")
                route.continue_()
            
            engine.intercept_network("**/api/**", handle_api)
        """
        self.page.route(pattern, handler)
