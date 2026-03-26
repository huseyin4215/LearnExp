"""
Selector Processor
Handles both CSS and XPath selectors with auto-detection
"""
from typing import List, Any, Optional, Union
from bs4 import BeautifulSoup, Tag
import logging
import re

logger = logging.getLogger(__name__)


class SelectorProcessor:
    """
    Universal selector processor
    Supports CSS and XPath with automatic detection
    """
    
    def __init__(self, default_type: str = 'css'):
        """
        Args:
            default_type: 'css', 'xpath', or 'mixed'
        """
        self.default_type = default_type
    
    def select_one(self, element: Union[BeautifulSoup, Tag], selector: str) -> Optional[Tag]:
        """
        Select single element using CSS or XPath
        
        Args:
            element: BeautifulSoup or Tag object
            selector: CSS or XPath selector
            
        Returns:
            First matching element or None
        """
        selector_type = self._detect_selector_type(selector)
        
        try:
            if selector_type == 'xpath':
                return self._select_xpath_one(element, selector)
            else:  # CSS
                return element.select_one(selector)
        except Exception as e:
            logger.error(f"Selector error ({selector}): {e}")
            return None
    
    def select_multiple(self, element: Union[BeautifulSoup, Tag], selector: str) -> List[Tag]:
        """
        Select multiple elements using CSS or XPath
        
        Args:
            element: BeautifulSoup or Tag object
            selector: CSS or XPath selector
            
        Returns:
            List of matching elements
        """
        selector_type = self._detect_selector_type(selector)
        
        try:
            if selector_type == 'xpath':
                return self._select_xpath_multiple(element, selector)
            else:  # CSS
                return element.select(selector)
        except Exception as e:
            logger.error(f"Selector error ({selector}): {e}")
            return []
    
    def get_attribute(self, element: Tag, attr: str) -> Optional[str]:
        """
        Get attribute value from element
        
        Args:
            element: BeautifulSoup Tag
            attr: Attribute name ('text', 'href', 'src', 'data-*', etc.)
            
        Returns:
            Attribute value or None
        """
        if not element:
            return None
        
        try:
            if attr == 'text':
                # Get text content
                return element.get_text(strip=True)
            
            elif attr == 'html':
                # Get inner HTML
                return str(element)
            
            elif attr == 'outerHTML':
                # Get outer HTML
                return str(element)
            
            else:
                # Get HTML attribute
                value = element.get(attr)
                if value:
                    return str(value).strip()
                return None
                
        except Exception as e:
            logger.error(f"Attribute extraction error ({attr}): {e}")
            return None
    
    def _detect_selector_type(self, selector: str) -> str:
        """
        Auto-detect if selector is CSS or XPath
        
        XPath indicators:
        - Starts with // or /
        - Contains [contains(@
        - Contains text()
        - Contains @attribute
        """
        if not selector:
            return 'css'
        
        # XPath patterns
        xpath_patterns = [
            r'^//',
            r'^/',
            r'\[@',
            r'text\(\)',
            r'@\w+',
            r'contains\(',
            r'starts-with\(',
            r'ancestor::',
            r'descendant::',
            r'following::',
            r'preceding::',
        ]
        
        for pattern in xpath_patterns:
            if re.search(pattern, selector):
                return 'xpath'
        
        return 'css'
    
    def _select_xpath_one(self, element: Union[BeautifulSoup, Tag], xpath: str) -> Optional[Tag]:
        """
        Select single element using XPath
        Uses lxml for XPath support
        """
        try:
            from lxml import etree, html as lxml_html
            
            # Convert BeautifulSoup to lxml
            if isinstance(element, BeautifulSoup):
                html_string = str(element)
            else:
                html_string = str(element)
            
            tree = lxml_html.fromstring(html_string)
            
            # Execute XPath
            result = tree.xpath(xpath)
            
            if result:
                # Convert back to BeautifulSoup
                if isinstance(result[0], str):
                    # Text node
                    return None
                else:
                    # Element node
                    html_str = etree.tostring(result[0], encoding='unicode')
                    return BeautifulSoup(html_str, 'lxml').find()
            
            return None
            
        except Exception as e:
            logger.error(f"XPath selection error: {e}")
            return None
    
    def _select_xpath_multiple(self, element: Union[BeautifulSoup, Tag], xpath: str) -> List[Tag]:
        """
        Select multiple elements using XPath
        """
        try:
            from lxml import etree, html as lxml_html
            
            # Convert to lxml
            if isinstance(element, BeautifulSoup):
                html_string = str(element)
            else:
                html_string = str(element)
            
            tree = lxml_html.fromstring(html_string)
            
            # Execute XPath
            results = tree.xpath(xpath)
            
            # Convert back to BeautifulSoup
            tags = []
            for result in results:
                if isinstance(result, str):
                    continue
                try:
                    html_str = etree.tostring(result, encoding='unicode')
                    tag = BeautifulSoup(html_str, 'lxml').find()
                    if tag:
                        tags.append(tag)
                except:
                    continue
            
            return tags
            
        except Exception as e:
            logger.error(f"XPath multiple selection error: {e}")
            return []
    
    def extract_with_fallback(self, element: Union[BeautifulSoup, Tag], 
                              selectors: List[str], attr: str = 'text') -> Optional[str]:
        """
        Try multiple selectors until one works
        
        Args:
            element: Element to search in
            selectors: List of selectors to try
            attr: Attribute to extract
            
        Returns:
            First successful extraction or None
        """
        for selector in selectors:
            elem = self.select_one(element, selector)
            if elem:
                value = self.get_attribute(elem, attr)
                if value:
                    return value
        return None
    
    def extract_nested(self, element: Union[BeautifulSoup, Tag], 
                       path: str, attr: str = 'text') -> Optional[str]:
        """
        Extract from nested path
        
        Args:
            element: Starting element
            path: Dot-separated path like "div.content > p.first"
            attr: Attribute to extract
            
        Returns:
            Extracted value or None
        """
        parts = path.split(' > ')
        current = element
        
        for part in parts:
            current = self.select_one(current, part.strip())
            if not current:
                return None
        
        return self.get_attribute(current, attr)
