"""
arXiv API Adapter
Handles XML-based arXiv API responses
"""
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
from typing import List, Dict, Any
import logging

from .base import BaseAPIAdapter, NormalizedArticle

logger = logging.getLogger(__name__)


class ArxivAdapter(BaseAPIAdapter):
    """
    Adapter for arXiv API
    Documentation: https://arxiv.org/help/api/index
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.base_url or 'http://export.arxiv.org/api/query'
        self.namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
    
    def build_query_params(self, query: str, max_results: int, **kwargs) -> Dict[str, Any]:
        """Build arXiv-specific query parameters"""
        params = {
            'search_query': f'all:{query}',
            'start': kwargs.get('start', 0),
            'max_results': min(max_results, 2000),  # arXiv limit
            'sortBy': kwargs.get('sort_by', 'submittedDate'),
            'sortOrder': kwargs.get('sort_order', 'descending')
        }
        
        # Add category filters if specified
        if self.config.categories:
            categories = [c.strip() for c in self.config.categories.split(',')]
            cat_query = ' OR '.join([f'cat:{cat}' for cat in categories])
            params['search_query'] = f"({params['search_query']}) AND ({cat_query})"
        
        return params
    
    def _make_request(self, params: Dict[str, Any]) -> str:
        """Make request to arXiv API"""
        response = requests.get(
            self.base_url,
            params=params,
            headers=self._build_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.content
    
    def parse_response(self, response_data: bytes) -> List[Dict[str, Any]]:
        """Parse XML response from arXiv"""
        root = ET.fromstring(response_data)
        ns = self.namespaces
        
        raw_articles = []
        for entry in root.findall('atom:entry', ns):
            try:
                raw_article = self._parse_entry(entry, ns)
                raw_articles.append(raw_article)
            except Exception as e:
                logger.error(f"Error parsing arXiv entry: {e}", exc_info=True)
                continue
        
        return raw_articles
    
    def _parse_entry(self, entry: ET.Element, ns: Dict[str, str]) -> Dict[str, Any]:
        """Parse single arXiv entry"""
        # Extract arXiv ID
        id_text = entry.find('atom:id', ns).text
        arxiv_id = id_text.split('/abs/')[-1]
        
        # Title
        title_elem = entry.find('atom:title', ns)
        title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else ''
        
        # Abstract
        summary_elem = entry.find('atom:summary', ns)
        abstract = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else ''
        
        # Authors
        authors = []
        for author in entry.findall('atom:author', ns):
            name_elem = author.find('atom:name', ns)
            if name_elem is not None:
                authors.append(name_elem.text)
        
        # Categories
        categories = []
        for cat in entry.findall('atom:category', ns):
            term = cat.get('term')
            if term:
                categories.append(term)
        
        # Published date
        published_elem = entry.find('atom:published', ns)
        published_str = published_elem.text if published_elem is not None else None
        
        # PDF link
        pdf_url = ''
        for link in entry.findall('atom:link', ns):
            if link.get('title') == 'pdf':
                pdf_url = link.get('href', '')
                break
        
        # URL
        url = id_text
        
        # DOI (if available)
        doi = ''
        doi_elem = entry.find('arxiv:doi', ns)
        if doi_elem is not None:
            doi = doi_elem.text
        
        return {
            'arxiv_id': arxiv_id,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'published': published_str,
            'categories': categories,
            'pdf_url': pdf_url,
            'url': url,
            'doi': doi
        }
    
    def normalize_article(self, raw_article: Dict[str, Any]) -> NormalizedArticle:
        """Normalize arXiv article to common format"""
        # Parse published date
        pub_date = None
        if raw_article.get('published'):
            try:
                pub_date = datetime.strptime(
                    raw_article['published'][:10],
                    '%Y-%m-%d'
                ).date()
            except Exception as e:
                logger.warning(f"Date parse error: {e}")
        
        # Format authors
        authors = [{'name': name} for name in raw_article.get('authors', [])]
        
        return NormalizedArticle(
            external_id=f"arxiv:{raw_article['arxiv_id']}",
            title=raw_article.get('title', ''),
            abstract=raw_article.get('abstract', ''),
            authors=authors,
            published_date=pub_date,
            source_name='arxiv',
            url=raw_article.get('url', ''),
            pdf_url=raw_article.get('pdf_url', ''),
            doi=raw_article.get('doi') or None,
            categories=raw_article.get('categories', []),
            keywords=raw_article.get('categories', []),
            raw_data={
                'source': 'arxiv',
                'arxiv_id': raw_article['arxiv_id'],
                'original_data': raw_article
            }
        )
