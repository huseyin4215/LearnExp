"""
Selenium Scraper Engine
Uses Selenium WebDriver for JavaScript-rendered sites
"""
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import time
import logging

from .base_engine import BaseScraperEngine, ScrapedItem
from ..processors.selector_processor import SelectorProcessor
from ..processors.date_parser import DateParser

logger = logging.getLogger(__name__)


class SeleniumScraperEngine(BaseScraperEngine):
    """
    Selenium scraping engine for JavaScript-rendered sites
    Best for: Dynamic content, SPAs, sites requiring JS execution
    
    Requirements:
        pip install selenium
        
    Drivers:
        Chrome: pip install webdriver-manager
        Or download from: https://chromedriver.chromium.org/
    """
    
    def setup(self):
        """Setup Selenium WebDriver"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Store Selenium imports
            self.By = By
            self.WebDriverWait = WebDriverWait
            self.EC = EC
            
            # Chrome options
            chrome_options = Options()
            
            # Headless mode (no GUI)
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # User agent
            chrome_options.add_argument(f'user-agent={self.config.user_agent}')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Disable images for faster loading (optional)
            prefs = {
                'profile.managed_default_content_settings.images': 2,
                'profile.default_content_setting_values.notifications': 2,
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            # Custom headers (limited support in Selenium)
            if self.config.custom_headers:
                # Note: Selenium has limited header support
                # Consider using Chrome DevTools Protocol for full header control
                pass
            
            # Initialize driver
            try:
                # Try with webdriver-manager (auto-downloads driver)
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except ImportError:
                # Fallback to system chromedriver
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Set timeouts
            self.driver.set_page_load_timeout(self.config.timeout_seconds)
            self.driver.implicitly_wait(10)
            
            # Initialize processors
            self.selector_processor = SelectorProcessor(self.config.selector_type)
            self.date_parser = DateParser(self.config.date_format)
            
            logger.info(f"Selenium engine setup complete for {self.config.name}")
            
        except ImportError as e:
            logger.error(f"Selenium not installed: {e}")
            raise Exception(
                "Selenium not installed. Install with: pip install selenium webdriver-manager"
            )
    
    def cleanup(self):
        """Close browser"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("Selenium driver closed")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
    
    def login(self) -> bool:
        """
        Handle form-based login with Selenium
        """
        if not self.config.requires_login:
            return True
        
        try:
            logger.info(f"Attempting login to {self.config.login_url}")
            
            # Navigate to login page
            self.driver.get(self.config.login_url)
            time.sleep(2)  # Wait for page load
            
            # Find username field
            username_field = self.driver.find_element(
                self.By.NAME, 
                self.config.login_username_field
            )
            username_field.clear()
            username_field.send_keys(self.config.username)
            
            # Find password field
            password_field = self.driver.find_element(
                self.By.NAME,
                self.config.login_password_field
            )
            password_field.clear()
            password_field.send_keys(self.config.password)
            
            # Find and click submit button
            submit_selector = self.config.login_submit_selector or 'button[type="submit"]'
            submit_button = self.driver.find_element(self.By.CSS_SELECTOR, submit_selector)
            submit_button.click()
            
            # Wait for redirect/login completion
            time.sleep(3)
            
            # Check if login successful
            current_url = self.driver.current_url
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
        Navigate to URL and return page source
        """
        try:
            # Delay before request
            time.sleep(self.config.delay_between_requests)
            
            # Navigate
            self.driver.get(url)
            
            # Wait for page to load (wait for body element)
            self.WebDriverWait(self.driver, self.config.timeout_seconds).until(
                self.EC.presence_of_element_located((self.By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Scroll to load lazy content (optional)
            self._scroll_page()
            
            # Update statistics
            self.requests_made += 1
            page_source = self.driver.page_source
            self.bytes_downloaded += len(page_source.encode('utf-8'))
            
            logger.info(f"Successfully fetched {url}")
            
            # Return page source for BeautifulSoup parsing
            from bs4 import BeautifulSoup
            return BeautifulSoup(page_source, 'lxml')
            
        except Exception as e:
            logger.error(f"Navigation error for {url}: {e}", exc_info=True)
            self.failed_urls.append(url)
            raise
    
    def _scroll_page(self):
        """Scroll page to load lazy content"""
        try:
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Scroll failed: {e}")
    
    def extract_items(self, page_content: Any) -> List[Dict[str, Any]]:
        """
        Extract items from page using configured selectors
        Same as HTMLEngine since we convert to BeautifulSoup
        """
        items = []
        selectors = self.config.selectors or {}
        
        # Get item container selector
        container_selector = selectors.get('item_container', 'article')
        
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
                    if field_name in ['item_container', 'pagination_next']:
                        continue
                    
                    # Extract field value
                    value = self._extract_field(item_elem, field_config)
                    item_data[field_name] = value
                
                items.append(item_data)
                
            except Exception as e:
                logger.error(f"Item extraction error: {e}", exc_info=True)
                continue
        
        return items
    
    def _extract_field(self, element: Any, field_config: Any) -> Any:
        """
        Extract single field from element
        Same as HTMLEngine
        """
        # Handle simple string selector
        if isinstance(field_config, str):
            field_config = {"selector": field_config, "attr": "text"}
        
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
                return self.selector_processor.get_attribute(elem, attr)
            return None
    
    def get_next_page_url(self, page_content: Any, current_page: int) -> Optional[str]:
        """
        Get next page URL based on pagination strategy
        Same as HTMLEngine
        """
        if self.config.pagination_type == 'none':
            return None
        
        elif self.config.pagination_type == 'url_pattern':
            # Use URL pattern
            if self.config.pagination_url_pattern:
                next_page = current_page + 1
                return self.config.pagination_url_pattern.replace('{page}', str(next_page))
            return None
        
        elif self.config.pagination_type == 'next_button':
            # Find next button
            selectors = self.config.selectors or {}
            next_selector = selectors.get('pagination_next', 'a.next, [rel="next"]')
            
            next_elem = self.selector_processor.select_one(page_content, next_selector)
            if next_elem:
                href = self.selector_processor.get_attribute(next_elem, 'href')
                if href:
                    return urljoin(self.config.base_url, href)
            return None
        
        elif self.config.pagination_type == 'page_numbers':
            # Find page number links
            selectors = self.config.selectors or {}
            page_selector = selectors.get('pagination_pages', '.pagination a')
            
            page_elements = self.selector_processor.select_multiple(page_content, page_selector)
            
            # Find next page number
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
        """
        Normalize raw extracted item to ScrapedItem format
        Same as HTMLEngine
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
        
        # Parse date
        pub_date = None
        if raw_item.get('published_date'):
            pub_date = self.date_parser.parse(raw_item['published_date'])
        
        # Parse categories
        categories = []
        cats_data = raw_item.get('categories', [])
        if isinstance(cats_data, list):
            categories = [str(c) for c in cats_data]
        elif isinstance(cats_data, str):
            categories = [c.strip() for c in cats_data.split(',') if c.strip()]
        
        # Generate external ID
        external_id = raw_item.get('external_id') or self._generate_external_id(
            raw_item.get('url', '') or raw_item.get('title', '')
        )
        
        return ScrapedItem(
            title=raw_item.get('title', ''),
            url=raw_item.get('url', ''),
            external_id=external_id,
            abstract=raw_item.get('abstract', ''),
            authors=authors,
            published_date=pub_date,
            source_name=self.config.name,
            categories=categories,
            keywords=raw_item.get('keywords', []),
            content_type=raw_item.get('content_type', 'article'),
            journal=raw_item.get('journal', ''),
            doi=raw_item.get('doi', ''),
            pdf_url=raw_item.get('pdf_url', ''),
            location=raw_item.get('location', ''),
            event_date=raw_item.get('event_date'),
            deadline=raw_item.get('deadline'),
            amount=raw_item.get('amount', ''),
            raw_data={
                'source': self.config.name,
                'engine': 'selenium',
                'original_data': raw_item
            }
        )
    
    def take_screenshot(self, filename: str = None):
        """
        Take screenshot (bonus feature)
        """
        if not filename:
            import datetime
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
