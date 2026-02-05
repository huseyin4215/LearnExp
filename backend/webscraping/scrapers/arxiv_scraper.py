import requests
from datetime import datetime
from .base import BaseScraper


class ArxivScraper(BaseScraper):
    """Scraper for arXiv.org"""
    
    def scrape(self):
        """Scrape articles from arXiv API"""
        base_url = self.config.base_url or "http://export.arxiv.org/api/query"
        
        params = {
            'search_query': self.config.search_query,
            'start': 0,
            'max_results': self.config.max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Extract articles
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', namespace)
            
            results = []
            for entry in entries:
                item = {
                    'id': entry.find('atom:id', namespace).text,
                    'title': entry.find('atom:title', namespace).text.strip(),
                    'summary': entry.find('atom:summary', namespace).text.strip(),
                    'published': entry.find('atom:published', namespace).text,

                    'authors': [
                        author.find('atom:name', namespace).text
                        for author in entry.findall('atom:author', namespace)
                    ],
                    'link': entry.find('atom:id', namespace).text,
                    'categories': [
                        cat.get('term')
                        for cat in entry.findall('atom:category', namespace)
                    ],
                }
                results.append(item)
            
            return results
            
        except Exception as e:
            print(f"Error scraping arXiv: {e}")
            return []
    
    def parse(self, raw_data):
        """Parse arXiv data into standardized format"""
        # Extract arXiv ID from URL
        arxiv_id = raw_data['id'].split('/abs/')[-1]
        
        # Parse published date
        try:
            published_date = datetime.fromisoformat(raw_data['published'].replace('Z', '+00:00')).date()
        except:
            published_date = None
        
        return {
            'external_id': f"arxiv_{arxiv_id}",
            'title': raw_data['title'],
            'description': raw_data['summary'],
            'authors': ', '.join(raw_data['authors'][:5]),  # Limit to first 5 authors
            'source': 'arXiv',
            'published_date': published_date,
            'url': raw_data['link'],
            'content_type': 'article',
            'tags': raw_data['categories'][:10],  # Limit tags
        }
