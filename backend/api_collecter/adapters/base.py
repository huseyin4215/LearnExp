"""
Base API Adapter - Abstract Base Class
All API adapters must inherit from this class
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class NormalizedArticle:
    """
    Normalized article structure - common format for all APIs
    This ensures consistency across different data sources
    """
    external_id: str
    title: str
    abstract: str = ""
    authors: List[Dict[str, str]] = field(default_factory=list)
    published_date: Optional[date] = None
    source_name: str = ""
    url: str = ""
    pdf_url: str = ""
    doi: Optional[str] = None
    journal: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    citation_count: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        # Convert date to string for JSON serialization
        if self.published_date:
            data['published_date'] = self.published_date
        return data
    
    def validate(self) -> bool:
        """Validate required fields"""
        if not self.external_id:
            logger.warning("Missing external_id")
            return False
        if not self.title or len(self.title.strip()) < 3:
            logger.warning(f"Invalid title for {self.external_id}")
            return False
        return True


class BaseAPIAdapter(ABC):
    """
    Abstract base class for all API adapters
    
    Responsibilities:
    - Build query parameters
    - Make HTTP requests
    - Parse responses (JSON/XML)
    - Normalize data to NormalizedArticle format
    - Handle errors and retries
    """
    
    def __init__(self, config):
        """
        Args:
            config: APISourceConfig model instance
        """
        self.config = config
        self.source_name = config.source_type
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.api_secret = config.api_secret
        self.timeout = 60
        
    @abstractmethod
    def build_query_params(self, query: str, max_results: int, **kwargs) -> Dict[str, Any]:
        """
        Build API-specific query parameters
        
        Args:
            query: Search query string
            max_results: Maximum number of results to fetch
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of query parameters
        """
        pass
    
    @abstractmethod
    def parse_response(self, response_data: Any) -> List[Dict[str, Any]]:
        """
        Parse API response to raw article data
        
        Args:
            response_data: Raw response from API (JSON dict or XML string)
            
        Returns:
            List of raw article dictionaries
        """
        pass
    
    @abstractmethod
    def normalize_article(self, raw_article: Dict[str, Any]) -> NormalizedArticle:
        """
        Normalize raw article data to NormalizedArticle format
        
        Args:
            raw_article: Raw article data from API
            
        Returns:
            NormalizedArticle instance
        """
        pass
    
    def fetch(self, query: str, max_results: int, **kwargs) -> List[NormalizedArticle]:
        """
        Main fetch method - orchestrates the entire fetch process
        
        Args:
            query: Search query
            max_results: Maximum results to fetch
            **kwargs: Additional parameters
            
        Returns:
            List of NormalizedArticle instances
        """
        try:
            # Build query parameters
            params = self.build_query_params(query, max_results, **kwargs)
            
            # Make request
            response_data = self._make_request(params)
            
            # Parse response
            raw_articles = self.parse_response(response_data)
            
            # Normalize articles
            normalized_articles = []
            for raw_article in raw_articles:
                try:
                    normalized = self.normalize_article(raw_article)
                    if normalized.validate():
                        normalized_articles.append(normalized)
                    else:
                        logger.warning(f"Invalid article skipped: {normalized.external_id}")
                except Exception as e:
                    logger.error(f"Normalization error: {e}", exc_info=True)
                    continue
            
            return normalized_articles
            
        except Exception as e:
            logger.error(f"Fetch error for {self.source_name}: {e}", exc_info=True)
            raise
    
    @abstractmethod
    def _make_request(self, params: Dict[str, Any]) -> Any:
        """
        Make HTTP request to API
        
        Args:
            params: Query parameters
            
        Returns:
            Response data (JSON dict or XML string)
        """
        pass
    
    def _build_headers(self) -> Dict[str, str]:
        """Build common HTTP headers"""
        headers = {
            'User-Agent': 'LearnExp Academic Platform/2.0 (https://learnexp.com; mailto:contact@learnexp.com)'
        }
        
        if self.api_key:
            # Different APIs use different auth headers
            # Override in subclasses if needed
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def _safe_get(self, data: Dict, *keys, default=None):
        """Safely get nested dictionary values"""
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, default)
            elif isinstance(data, list) and len(data) > 0:
                data = data[0] if isinstance(key, int) else default
            else:
                return default
        return data if data is not None else default
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(source={self.source_name})>"
