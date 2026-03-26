"""
Generic Dynamic API Fetcher
Tamamen konfigürasyona dayalı, herhangi bir API için çalışır
"""
import requests
import xml.etree.ElementTree as ET
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


class GenericAPIFetcher:
    """
    Tamamen dinamik API fetcher
    Admin panelinden yapılan konfigürasyona göre herhangi bir API'den veri çeker
    """
    
    def __init__(self, config):
        """
        Args:
            config: APISourceConfig model instance
        """
        self.config = config
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup HTTP session with auth and headers"""
        # Base headers
        headers = {
            'User-Agent': 'LearnExp Academic Platform/2.0',
            'Accept': 'application/json, application/xml, text/xml, */*'
        }
        
        # Custom headers
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)
        
        # Authentication
        if self.config.auth_type == 'api_key_header':
            headers[self.config.api_key_header_name] = self.config.api_key
        elif self.config.auth_type == 'bearer_token':
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        elif self.config.auth_type == 'basic_auth':
            from requests.auth import HTTPBasicAuth
            self.session.auth = HTTPBasicAuth(
                self.config.api_key,
                self.config.api_secret
            )
        
        self.session.headers.update(headers)
    
    def fetch(self, query: str = None, max_results: int = None) -> Dict[str, Any]:
        """
        Ana fetch metodu
        
        Returns:
            {
                'success': bool,
                'articles': List[Dict],
                'total_found': int,
                'saved': int,
                'updated': int,
                'skipped': int,
                'error': str (if failed)
            }
        """
        from ..models import APIFetchLog, Article
        
        # Create fetch log
        fetch_log = APIFetchLog.objects.create(
            api_config=self.config,
            status='started',
            request_method=self.config.http_method
        )
        
        start_time = time.time()
        
        try:
            # Build request parameters
            search_query = query or self.config.default_search_query
            result_limit = max_results or self.config.max_results_per_request
            
            params = self._build_params(search_query, result_limit)
            
            # Log request details
            fetch_log.request_params = params
            fetch_log.request_url = self.config.base_url
            fetch_log.status = 'fetching'
            fetch_log.save()
            
            # Make request
            response = self._make_request(params)
            
            # Log response
            fetch_log.response_status_code = response.status_code
            fetch_log.response_size_bytes = len(response.content)
            fetch_log.status = 'parsing'
            fetch_log.save()
            
            # Parse response
            raw_articles = self._parse_response(response)
            
            fetch_log.articles_found = len(raw_articles)
            fetch_log.status = 'saving'
            fetch_log.save()
            
            # Normalize and save articles
            saved, updated, skipped = self._save_articles(raw_articles)
            
            # Complete successfully
            duration = time.time() - start_time
            fetch_log.status = 'success'
            fetch_log.articles_saved = saved
            fetch_log.articles_updated = updated
            fetch_log.articles_skipped = skipped
            fetch_log.completed_at = timezone.now()
            fetch_log.duration_seconds = duration
            fetch_log.save()
            
            # Update config
            self.config.last_fetch = timezone.now()
            self.config.next_fetch = timezone.now() + timedelta(hours=self.config.fetch_interval_hours)
            self.config.total_articles_fetched += saved
            self.config.total_requests_made += 1
            self.config.last_error = ''
            self.config.save()
            
            return {
                'success': True,
                'articles': raw_articles,
                'total_found': len(raw_articles),
                'saved': saved,
                'updated': updated,
                'skipped': skipped,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"Fetch failed for {self.config.name}: {e}", exc_info=True)
            
            duration = time.time() - start_time
            fetch_log.status = 'failed'
            fetch_log.error_message = str(e)
            fetch_log.error_details = {'exception': str(type(e).__name__)}
            fetch_log.completed_at = timezone.now()
            fetch_log.duration_seconds = duration
            fetch_log.save()
            
            # Update config
            self.config.last_error = str(e)
            self.config.last_error_at = timezone.now()
            self.config.save()
            
            return {
                'success': False,
                'error': str(e),
                'articles': [],
                'total_found': 0
            }
    
    def _build_params(self, query: str, max_results: int) -> Dict[str, Any]:
        """
        Build request parameters from config
        Supports variable substitution
        """
        params = {}
        
        # Start with query_params from config
        if self.config.query_params:
            params = self.config.query_params.copy()
        
        # Variable substitution
        variables = {
            '{search_query}': query,
            '{max_results}': str(max_results),
            '{categories}': self.config.categories or '',
        }
        
        # Replace variables in params
        for key, value in params.items():
            if isinstance(value, str):
                for var, replacement in variables.items():
                    value = value.replace(var, replacement)
                params[key] = value
        
        # Add API key as parameter if needed
        if self.config.auth_type == 'api_key_param':
            params[self.config.api_key_param_name] = self.config.api_key
        
        return params
    
    def _make_request(self, params: Dict[str, Any]) -> requests.Response:
        """Make HTTP request"""
        # Rate limiting
        time.sleep(self.config.request_delay_seconds)
        
        if self.config.http_method == 'GET':
            response = self.session.get(
                self.config.base_url,
                params=params,
                timeout=self.config.timeout_seconds,
                verify=self.config.verify_ssl
            )
        else:  # POST
            body = self.config.request_body_template.copy() if self.config.request_body_template else {}
            response = self.session.post(
                self.config.base_url,
                json=body,
                params=params,
                timeout=self.config.timeout_seconds,
                verify=self.config.verify_ssl
            )
        
        response.raise_for_status()
        return response
    
    def _parse_response(self, response: requests.Response) -> List[Dict[str, Any]]:
        """
        Parse response based on format
        """
        if self.config.response_format == 'json':
            return self._parse_json(response)
        elif self.config.response_format == 'xml':
            return self._parse_xml(response)
        elif self.config.response_format == 'rss':
            return self._parse_rss(response)
        else:
            raise ValueError(f"Unsupported response format: {self.config.response_format}")
    
    def _parse_json(self, response: requests.Response) -> List[Dict[str, Any]]:
        """Parse JSON response"""
        data = response.json()
        
        # Navigate to data array using path
        items = self._get_nested_value(data, self.config.response_data_path)
        
        if not isinstance(items, list):
            logger.warning(f"Expected list at path '{self.config.response_data_path}', got {type(items)}")
            return []
        
        # Normalize each item
        normalized_articles = []
        for item in items:
            try:
                normalized = self._normalize_article(item)
                if normalized:
                    normalized_articles.append(normalized)
            except Exception as e:
                logger.error(f"Error normalizing article: {e}", exc_info=True)
                continue
        
        return normalized_articles
    
    @staticmethod
    def _strip_namespaces(root: ET.Element) -> ET.Element:
        """
        Strip all XML namespace prefixes from the element tree.
        Converts tags like {http://www.w3.org/2005/Atom}entry -> entry
        Works for ANY XML API with any namespace.
        """
        for elem in root.iter():
            # Strip namespace from tag
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]
            # Strip namespace from attributes
            new_attrib = {}
            for attr_key, attr_val in elem.attrib.items():
                if '}' in attr_key:
                    attr_key = attr_key.split('}', 1)[1]
                new_attrib[attr_key] = attr_val
            elem.attrib = new_attrib
        return root

    def _parse_xml(self, response: requests.Response) -> List[Dict[str, Any]]:
        """
        Parse XML response with automatic namespace handling.
        
        Steps:
        1. Parse XML content
        2. Strip ALL namespace prefixes from the tree
        3. Use response_data_path to find item elements
        4. Convert each item to a dict
        5. Normalize using field_mappings
        """
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return []
        
        # Step 2: Strip all namespaces for clean path resolution
        self._strip_namespaces(root)
        
        # Step 3: Find items using response_data_path
        data_path = self.config.response_data_path
        if not data_path:
            logger.warning("No response_data_path configured for XML source")
            return []
        
        # Convert dot notation to XPath: "feed.entry" -> ".//feed/entry", "entry" -> ".//entry"
        path_parts = data_path.split('.')
        xpath = './/' + '/'.join(path_parts)
        
        items = root.findall(xpath)
        
        # Fallback: try just the last path component
        if not items and len(path_parts) > 1:
            items = root.findall('.//' + path_parts[-1])
            logger.info(f"Fallback XPath found {len(items)} items using '{path_parts[-1]}'")
        
        logger.info(f"XML parser found {len(items)} items at path '{data_path}'")
        
        # Step 4 & 5: Convert and normalize
        normalized_articles = []
        for item in items:
            try:
                item_dict = self._xml_to_dict(item)
                normalized = self._normalize_article(item_dict)
                if normalized:
                    normalized_articles.append(normalized)
            except Exception as e:
                logger.error(f"Error normalizing XML article: {e}", exc_info=True)
                continue
        
        return normalized_articles
    
    def _parse_rss(self, response: requests.Response) -> List[Dict[str, Any]]:
        """Parse RSS feed"""
        root = ET.fromstring(response.content)
        
        # RSS items are typically at channel/item
        items = root.findall('.//item')
        
        normalized_articles = []
        for item in items:
            try:
                item_dict = self._xml_to_dict(item)
                normalized = self._normalize_article(item_dict)
                if normalized:
                    normalized_articles.append(normalized)
            except Exception as e:
                logger.error(f"Error normalizing RSS article: {e}", exc_info=True)
                continue
        
        return normalized_articles
    
    def _normalize_article(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize article using field mappings
        """
        if not self.config.field_mappings:
            logger.warning("No field mappings configured")
            return None
        
        normalized = {}
        # Import BeautifulSoup
        from bs4 import BeautifulSoup
        
        # Map each field
        for target_field, source_path in self.config.field_mappings.items():
            value = self._get_nested_value(raw_data, source_path)
            
            # Special handling for specific fields
            if target_field == 'authors':
                value = self._parse_authors(value)
            elif target_field == 'published_date':
                value = self._parse_date(value)
            elif target_field in ['categories', 'keywords']:
                value = self._ensure_list(value)
            elif target_field in ['title', 'abstract']:
                if isinstance(value, str) and value:
                    value = BeautifulSoup(value, "html.parser").get_text(separator=" ").strip().replace('\n', ' ')
            
            normalized[target_field] = value
        
        # Ensure required fields
        if not normalized.get('external_id'):
            normalized['external_id'] = f"{self.config.name}:{hash(str(raw_data))}"
        
        if not normalized.get('title'):
            logger.warning("Article missing title, skipping")
            return None
        
        # Add raw data
        normalized['raw_data'] = {
            'source': self.config.name,
            'original_data': raw_data,
            'fetched_at': timezone.now().isoformat()
        }
        
        return normalized
    
    def _get_nested_value(self, data: Any, path: str, default=None) -> Any:
        """
        Get value from nested dict/object using dot notation.
        
        Supports automatic list traversal:
        - 'author.name' on a list of author dicts -> extracts 'name' from each
        - 'metadata.title' -> data['metadata']['title']
        - 'items.0.name' -> data['items'][0]['name']
        
        This is critical for XML APIs where elements like <author> may
        appear multiple times, creating a list in the dict representation.
        """
        if not path:
            return data
        
        keys = path.split('.')
        current = data
        
        for i, key in enumerate(keys):
            if isinstance(current, dict):
                current = current.get(key, default)
            elif isinstance(current, list):
                if key.isdigit():
                    # Direct index access
                    idx = int(key)
                    current = current[idx] if idx < len(current) else default
                else:
                    # Auto-traverse: extract 'key' from each item in list
                    remaining_path = '.'.join(keys[i:])
                    result = []
                    for item in current:
                        val = self._get_nested_value(item, remaining_path, None)
                        if val is not None:
                            if isinstance(val, list):
                                result.extend(val)
                            else:
                                result.append(val)
                    return result if result else default
            else:
                return default
            
            if current is None:
                return default
        
        return current
    
    def _parse_authors(self, value: Any) -> List[Dict[str, str]]:
        """Parse authors based on configuration"""
        if not value:
            return []
        
        if self.config.author_field_type == 'string':
            # Comma-separated string
            if isinstance(value, str):
                names = [n.strip() for n in value.split(',')]
                return [{'name': name} for name in names if name]
        
        elif self.config.author_field_type == 'array':
            # Simple array of strings
            if isinstance(value, list):
                return [{'name': str(author)} for author in value]
        
        elif self.config.author_field_type == 'object_array':
            # Array of objects with name field
            if isinstance(value, list):
                name_field = self.config.author_name_field or 'name'
                authors = []
                for author in value:
                    if isinstance(author, dict):
                        # Try configured name field first
                        name = author.get(name_field, '')
                        # If name is empty, try combining given + family (CrossRef format)
                        if not name:
                            given = author.get('given', '')
                            family = author.get('family', '')
                            if given or family:
                                name = f"{given} {family}".strip()
                        # Still empty? Try 'display_name' (OpenAlex format)
                        if not name:
                            name = author.get('display_name', '')
                        if name:
                            authors.append({'name': str(name)})
                    else:
                        authors.append({'name': str(author)})
                return authors
        
        return []
    
    def _parse_date(self, value: Any) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not value:
            return None
        
        try:
            # Handle CrossRef date-parts format: {"date-parts": [[2023, 10, 15]]}
            if isinstance(value, dict):
                date_parts = value.get('date-parts')
                if date_parts and isinstance(date_parts, list) and len(date_parts) > 0:
                    parts = date_parts[0]  # First date-parts entry
                    if isinstance(parts, list) and len(parts) >= 1:
                        year = int(parts[0]) if parts[0] else None
                        month = int(parts[1]) if len(parts) > 1 and parts[1] else 1
                        day = int(parts[2]) if len(parts) > 2 and parts[2] else 1
                        if year and 1900 <= year <= 2100:  # Sanity check
                            from datetime import date as date_cls
                            return date_cls(year, month, day)
                return None
            
            # Handle list format directly: [[2023, 10, 15]]
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], list):
                    parts = value[0]
                elif len(value) > 0 and isinstance(value[0], int):
                    parts = value
                else:
                    return None
                year = int(parts[0]) if parts[0] else None
                month = int(parts[1]) if len(parts) > 1 and parts[1] else 1
                day = int(parts[2]) if len(parts) > 2 and parts[2] else 1
                if year and 1900 <= year <= 2100:
                    from datetime import date as date_cls
                    return date_cls(year, month, day)
                return None
            
            if isinstance(value, str):
                # Try parsing with configured format
                if self.config.date_format:
                    try:
                        dt = datetime.strptime(value, self.config.date_format)
                        return dt.date()
                    except:
                        pass
                
                # Try common formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        dt = datetime.strptime(value[:len(fmt.replace('%Y','2000').replace('%m','01').replace('%d','01').replace('%H','00').replace('%M','00').replace('%S','00').replace('%Z','Z'))], fmt)
                        return dt.date()
                    except:
                        continue
                
                # Last resort: try just the first 10 chars as YYYY-MM-DD
                try:
                    dt = datetime.strptime(value[:10], '%Y-%m-%d')
                    return dt.date()
                except:
                    pass
            
            return None
        except Exception as e:
            logger.warning(f"Date parse error: {e}")
            return None
    
    def _ensure_list(self, value: Any) -> List:
        """Ensure value is a list"""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            # Try splitting by comma
            return [v.strip() for v in value.split(',') if v.strip()]
        return [str(value)]
    
    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Convert XML element to a Python dictionary.
        
        Rules:
        - Element text becomes the value directly if no children
        - Attributes are stored with '@' prefix (e.g., @href, @term)
        - Multiple children with the same tag become a list
        - Namespaces are already stripped by _strip_namespaces
        
        Example XML:
            <author>
                <name>John Doe</name>
            </author>
        Becomes:
            {'name': 'John Doe'}
        
        Example XML:
            <category term="cs.AI" />
        Becomes:
            {'@term': 'cs.AI'}
        """
        result = {}
        
        # Add attributes with @ prefix
        for attr_key, attr_val in element.attrib.items():
            result[f'@{attr_key}'] = attr_val
            # Also store without @ for simpler field_mapping access
            result[attr_key] = attr_val
        
        # Add text content
        if element.text and element.text.strip():
            result['_text'] = element.text.strip()
        
        # Process children
        for child in element:
            tag = child.tag  # Already namespace-stripped
            child_data = self._xml_to_dict(child)
            
            if tag in result:
                # Multiple children with same tag -> make it a list
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_data)
            else:
                result[tag] = child_data
        
        # If element has ONLY text (no children, no attributes), return text directly
        if len(result) == 1 and '_text' in result:
            return result['_text']
        
        return result
    
    def _save_articles(self, raw_articles: List[Dict]) -> tuple:
        """Save normalized articles to database"""
        from ..models import Article
        
        saved = 0
        updated = 0
        skipped = 0
        
        for article_data in raw_articles:
            try:
                external_id = article_data.get('external_id')
                if not external_id:
                    skipped += 1
                    continue
                
                # Check if exists
                existing = Article.objects.filter(external_id=external_id).first()
                
                if existing:
                    # Update
                    for key, value in article_data.items():
                        if key != 'external_id' and value is not None:
                            setattr(existing, key, value)
                    existing.save()
                    updated += 1
                else:
                    # Ensure abstract is not None (NOT NULL constraint)
                    if article_data.get('abstract') is None:
                        article_data['abstract'] = ''
                    # Create new
                    Article.objects.create(
                        api_source=self.config,
                        **article_data
                    )
                    saved += 1
                    
            except Exception as e:
                logger.error(f"Article save error: {e}", exc_info=True)
                skipped += 1
        
        return saved, updated, skipped


# Helper functions
def fetch_from_source(config_id: int, query: str = None, max_results: int = None) -> Dict:
    """
    Fetch from specific API source
    """
    from ..models import APISourceConfig
    
    try:
        config = APISourceConfig.objects.get(id=config_id)
        if not config.is_active:
            return {'success': False, 'error': 'API source is not active'}
        
        fetcher = GenericAPIFetcher(config)
        return fetcher.fetch(query, max_results)
        
    except APISourceConfig.DoesNotExist:
        return {'success': False, 'error': 'API source not found'}
    except Exception as e:
        logger.error(f"Fetch error: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def fetch_all_active_sources() -> List[Dict]:
    """Fetch from all active sources"""
    from ..models import APISourceConfig
    
    results = []
    active_configs = APISourceConfig.objects.filter(is_active=True)
    
    for config in active_configs:
        result = fetch_from_source(config.id)
        results.append({
            'source': config.name,
            'result': result
        })
    
    return results
