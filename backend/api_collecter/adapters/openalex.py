"""
OpenAlex API Adapter
Handles JSON-based OpenAlex API responses
"""
import requests
from datetime import datetime
from typing import List, Dict, Any
import logging

from .base import BaseAPIAdapter, NormalizedArticle

logger = logging.getLogger(__name__)


class OpenAlexAdapter(BaseAPIAdapter):
    """
    Adapter for OpenAlex API
    Documentation: https://docs.openalex.org/
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.base_url or 'https://api.openalex.org/works'
    
    def build_query_params(self, query: str, max_results: int, **kwargs) -> Dict[str, Any]:
        """Build OpenAlex-specific query parameters"""
        params = {
            'search': query,
            'per_page': min(max_results, 200),  # OpenAlex max is 200
            'page': kwargs.get('page', 1),
            'sort': kwargs.get('sort', 'publication_date:desc'),
            'select': 'id,title,abstract_inverted_index,authorships,publication_date,doi,primary_location,cited_by_count,concepts,biblio'
        }
        
        # Add email for polite pool (higher rate limits)
        if self.api_key:  # Use api_key field for email
            params['mailto'] = self.api_key
        
        # Add filters if specified
        if self.config.categories:
            # OpenAlex uses concept filters
            params['filter'] = f"concepts.display_name:{self.config.categories}"
        
        return params
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to OpenAlex API"""
        headers = self._build_headers()
        # OpenAlex doesn't use Authorization header
        headers.pop('Authorization', None)
        
        response = requests.get(
            self.base_url,
            params=params,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def parse_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse JSON response from OpenAlex"""
        return response_data.get('results', [])
    
    def normalize_article(self, raw_article: Dict[str, Any]) -> NormalizedArticle:
        """Normalize OpenAlex article to common format"""
        # Extract OpenAlex ID
        openalex_id = raw_article.get('id', '').replace('https://openalex.org/', '')
        
        # Title
        title = raw_article.get('title', '')
        
        # Abstract from inverted index
        abstract = self._reconstruct_abstract(
            raw_article.get('abstract_inverted_index', {})
        )
        
        # Authors
        authors = self._extract_authors(raw_article.get('authorships', []))
        
        # Published date
        pub_date = None
        if raw_article.get('publication_date'):
            try:
                pub_date = datetime.strptime(
                    raw_article['publication_date'],
                    '%Y-%m-%d'
                ).date()
            except Exception as e:
                logger.warning(f"Date parse error: {e}")
        
        # DOI
        doi = raw_article.get('doi', '')
        if doi and doi.startswith('https://doi.org/'):
            doi = doi.replace('https://doi.org/', '')
        
        # Primary location (journal, PDF)
        primary_loc = raw_article.get('primary_location', {}) or {}
        source = primary_loc.get('source', {}) or {}
        journal = source.get('display_name', '')
        pdf_url = primary_loc.get('pdf_url', '') or ''
        
        # URL
        url = raw_article.get('id', '')
        
        # Categories (concepts)
        concepts = raw_article.get('concepts', []) or []
        categories = [c.get('display_name', '') for c in concepts[:5]]
        
        # Citation count
        citation_count = raw_article.get('cited_by_count', 0) or 0
        
        # Biblio info
        biblio = raw_article.get('biblio', {}) or {}
        volume = biblio.get('volume', '') or ''
        issue = biblio.get('issue', '') or ''
        first_page = biblio.get('first_page', '') or ''
        last_page = biblio.get('last_page', '') or ''
        pages = f"{first_page}-{last_page}" if first_page and last_page else (first_page or '')
        
        return NormalizedArticle(
            external_id=f"openalex:{openalex_id}",
            title=title,
            abstract=abstract,
            authors=authors,
            published_date=pub_date,
            source_name='openalex',
            url=url,
            pdf_url=pdf_url,
            doi=doi if doi else None,
            journal=journal,
            volume=volume,
            issue=issue,
            pages=pages,
            categories=categories,
            keywords=categories,
            citation_count=citation_count,
            raw_data={
                'source': 'openalex',
                'openalex_id': openalex_id,
                'original_data': raw_article
            }
        )
    
    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """Reconstruct abstract from inverted index"""
        if not inverted_index:
            return ''
        
        try:
            # Find max position
            max_pos = max([max(positions) for positions in inverted_index.values()])
            
            # Create word list
            word_list = [''] * (max_pos + 1)
            
            # Fill positions
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_list[pos] = word
            
            # Join and return
            return ' '.join(word_list)
        except Exception as e:
            logger.error(f"Abstract reconstruction error: {e}")
            return ''
    
    def _extract_authors(self, authorships: List[Dict]) -> List[Dict[str, str]]:
        """Extract author information"""
        authors = []
        for authorship in authorships:
            author_info = authorship.get('author', {}) or {}
            author = {
                'name': author_info.get('display_name', ''),
            }
            
            # Add ORCID if available
            orcid = author_info.get('orcid', '')
            if orcid:
                author['orcid'] = orcid.replace('https://orcid.org/', '')
            
            # Add institution if available
            institutions = authorship.get('institutions', [])
            if institutions:
                inst = institutions[0]
                author['institution'] = inst.get('display_name', '')
            
            authors.append(author)
        
        return authors
