"""Base API Fetcher class"""
import requests
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Tüm API fetcher'lar için temel sınıf"""
    
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LearnExp Academic Research Bot/1.0'
        })
    
    @abstractmethod
    def fetch_articles(self, query: str = None, max_results: int = None) -> List[Dict[str, Any]]:
        """Makaleleri çek - Alt sınıflar implemente etmeli"""
        pass
    
    @abstractmethod
    def parse_article(self, raw_data: Dict) -> Dict[str, Any]:
        """Ham veriyi standart formata dönüştür"""
        pass
    
    def make_request(self, url: str, params: Dict = None, method: str = 'GET') -> Optional[requests.Response]:
        """HTTP isteği yap"""
        try:
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, json=params, timeout=30)
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_headers(self) -> Dict[str, str]:
        """API için gerekli header'ları döndür"""
        headers = {}
        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        return headers

