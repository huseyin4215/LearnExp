"""
Dinamik API Fetcher Servisi
Admin panelinden eklenen API kaynaklarını dinamik olarak çeker
"""
import requests
import xml.etree.ElementTree as ET
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


class APIFetcherService:
    """
    Dinamik API Fetcher - Admin panelinden eklenen kaynaklara göre çalışır
    """
    
    # Her API türü için fetcher fonksiyonları
    FETCHER_MAP = {
        'arxiv': '_fetch_arxiv',
        'openalex': '_fetch_openalex',
        'crossref': '_fetch_crossref',
        'semantic_scholar': '_fetch_semantic_scholar',
        'pubmed': '_fetch_pubmed',
        'core': '_fetch_core',
        'doaj': '_fetch_doaj',
        'custom': '_fetch_custom',
    }
    
    def __init__(self, api_config):
        """
        Args:
            api_config: APISourceConfig model instance
        """
        self.config = api_config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LearnExp Academic Research Platform/1.0 (https://learnexp.com)'
        })
        
        # API key varsa ekle
        if api_config.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_config.api_key}'
            })
    
    def fetch(self, query: str = None, max_results: int = None) -> Dict[str, Any]:
        """
        API'den makale çek
        
        Returns:
            {
                'success': bool,
                'articles': List[Dict],
                'total_found': int,
                'error': str (if failed)
            }
        """
        from ..models import APIFetchLog, Article
        
        # Log başlat
        fetch_log = APIFetchLog.objects.create(
            api_config=self.config,
            status='started'
        )
        
        start_time = time.time()
        
        try:
            # Sorgu belirleme
            search_query = query or self.config.search_query
            result_limit = max_results or self.config.max_results_per_request
            
            # API türüne göre fetcher seç
            fetcher_method = self.FETCHER_MAP.get(self.config.source_type)
            if not fetcher_method:
                raise ValueError(f"Desteklenmeyen API türü: {self.config.source_type}")
            
            # Fetch işlemi
            fetch_log.status = 'fetching'
            fetch_log.save()
            
            fetcher = getattr(self, fetcher_method)
            raw_articles = fetcher(search_query, result_limit)
            
            # İşleme
            fetch_log.status = 'processing'
            fetch_log.articles_found = len(raw_articles)
            fetch_log.save()
            
            # Makaleleri kaydet
            saved, updated, skipped = self._save_articles(raw_articles)
            
            # Başarılı tamamla
            duration = time.time() - start_time
            fetch_log.status = 'success'
            fetch_log.articles_saved = saved
            fetch_log.articles_updated = updated
            fetch_log.articles_skipped = skipped
            fetch_log.completed_at = timezone.now()
            fetch_log.duration_seconds = duration
            fetch_log.save()
            
            # Config güncelle
            self.config.last_fetch = timezone.now()
            self.config.next_fetch = timezone.now() + timedelta(hours=self.config.fetch_interval_hours)
            self.config.total_articles_fetched += saved
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
            logger.error(f"Fetch failed for {self.config.name}: {e}")
            fetch_log.status = 'failed'
            fetch_log.error_message = str(e)
            fetch_log.completed_at = timezone.now()
            fetch_log.duration_seconds = time.time() - start_time
            fetch_log.save()
            
            return {
                'success': False,
                'error': str(e),
                'articles': [],
                'total_found': 0
            }
    
    def _save_articles(self, raw_articles: List[Dict]) -> tuple:
        """Makaleleri veritabanına kaydet"""
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
                
                # Var mı kontrol et
                existing = Article.objects.filter(external_id=external_id).first()
                
                if existing:
                    # Güncelle
                    for key, value in article_data.items():
                        if key != 'external_id' and value:
                            setattr(existing, key, value)
                    existing.save()
                    updated += 1
                else:
                    # Yeni oluştur
                    Article.objects.create(
                        api_source=self.config,
                        **article_data
                    )
                    saved += 1
                    
            except Exception as e:
                logger.error(f"Article save error: {e}")
                skipped += 1
        
        return saved, updated, skipped
    
    # ==================== API FETCHER'LAR ====================
    
    def _fetch_arxiv(self, query: str, max_results: int) -> List[Dict]:
        """arXiv API'den makale çek"""
        base_url = self.config.base_url or 'http://export.arxiv.org/api/query'
        
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        # Kategoriler varsa ekle
        if self.config.categories:
            categories = [c.strip() for c in self.config.categories.split(',')]
            cat_query = ' OR '.join([f'cat:{cat}' for cat in categories])
            params['search_query'] = f"({params['search_query']}) AND ({cat_query})"
        
        response = self.session.get(base_url, params=params, timeout=60)
        response.raise_for_status()
        
        # XML parse
        # Strip namespaces for easier parsing across generic Atom feeds
        content_str = response.content.decode('utf-8')
        root = ET.fromstring(content_str)
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]
        
        articles = []
        # Import BeautifulSoup for HTML cleanup
        from bs4 import BeautifulSoup

        for entry in root.findall('entry'):
            try:
                # ID çıkar
                id_elem = entry.find('id')
                arxiv_id = id_elem.text.split('/abs/')[-1] if id_elem is not None else ''
                
                # Yazarlar
                authors = []
                for author in entry.findall('author'):
                    name = author.find('name')
                    if name is not None and name.text:
                        authors.append({'name': name.text})
                
                # Kategoriler
                categories = []
                for cat in entry.findall('category'):
                    term = cat.get('term')
                    if term:
                        categories.append(term)
                
                # PDF link
                pdf_url = ''
                for link in entry.findall('link'):
                    if link.get('title') == 'pdf':
                        pdf_url = link.get('href', '')
                        break
                
                # Tarih parse
                pub_elem = entry.find('published')
                published = pub_elem.text if pub_elem is not None else ''
                pub_date = datetime.strptime(published[:10], '%Y-%m-%d').date() if published else None
                
                # Title & Abstract parse/cleanup
                title_elem = entry.find('title')
                raw_title = title_elem.text if title_elem is not None else ''
                clean_title = BeautifulSoup(raw_title, "html.parser").get_text(separator=" ").strip().replace('\n', ' ')

                summary_elem = entry.find('summary')
                raw_summary = summary_elem.text if summary_elem is not None else ''
                clean_summary = BeautifulSoup(raw_summary, "html.parser").get_text(separator=" ").strip().replace('\n', ' ')

                article = {
                    'external_id': f'arxiv:{arxiv_id}',
                    'title': clean_title,
                    'abstract': clean_summary,
                    'authors': authors,
                    'published_date': pub_date,
                    'url': id_elem.text if id_elem is not None else '',
                    'pdf_url': pdf_url,
                    'categories': categories,
                    'keywords': categories,
                    'doi': '',
                    'raw_data': {
                        'source': 'arxiv',
                        'arxiv_id': arxiv_id,
                        'fetched_at': timezone.now().isoformat()
                    }
                }
                articles.append(article)
                
            except Exception as e:
                logger.error(f"arXiv article parse error: {e}")
                continue
        
        return articles
    
    def _fetch_openalex(self, query: str, max_results: int) -> List[Dict]:
        """OpenAlex API'den makale çek"""
        base_url = self.config.base_url or 'https://api.openalex.org/works'
        
        params = {
            'search': query,
            'per_page': min(max_results, 200),  # OpenAlex max 200
            'sort': 'publication_date:desc',
            'select': 'id,title,abstract_inverted_index,authorships,publication_date,doi,primary_location,cited_by_count,concepts'
        }
        
        # Email varsa ekle (daha yüksek rate limit)
        if self.config.api_key:
            params['mailto'] = self.config.api_key
        
        response = self.session.get(base_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for work in data.get('results', []):
            try:
                # Abstract'ı inverted index'ten oluştur
                abstract = ''
                if work.get('abstract_inverted_index'):
                    abstract_parts = []
                    inv_index = work['abstract_inverted_index']
                    max_pos = max([max(positions) for positions in inv_index.values()]) if inv_index else 0
                    word_list = [''] * (max_pos + 1)
                    for word, positions in inv_index.items():
                        for pos in positions:
                            word_list[pos] = word
                    abstract = ' '.join(word_list)
                
                # Yazarlar
                authors = []
                for authorship in work.get('authorships', []):
                    author_info = authorship.get('author', {})
                    authors.append({
                        'name': author_info.get('display_name', ''),
                        'orcid': author_info.get('orcid', '')
                    })
                
                # Kategoriler/Concepts
                categories = [c.get('display_name') for c in work.get('concepts', [])[:5]]
                
                # DOI temizle
                doi = work.get('doi', '') or ''
                if doi.startswith('https://doi.org/'):
                    doi = doi.replace('https://doi.org/', '')
                
                # Tarih
                pub_date = None
                if work.get('publication_date'):
                    try:
                        pub_date = datetime.strptime(work['publication_date'], '%Y-%m-%d').date()
                    except:
                        pass
                
                # Journal
                journal = ''
                primary_loc = work.get('primary_location', {})
                if primary_loc and primary_loc.get('source'):
                    journal = primary_loc['source'].get('display_name', '')
                
                article = {
                    'external_id': work.get('id', '').replace('https://openalex.org/', 'openalex:'),
                    'title': work.get('title', ''),
                    'abstract': abstract,
                    'authors': authors,
                    'published_date': pub_date,
                    'doi': doi if doi else None,
                    'url': work.get('id', ''),
                    'pdf_url': primary_loc.get('pdf_url', '') if primary_loc else '',
                    'journal': journal,
                    'citation_count': work.get('cited_by_count', 0),
                    'categories': categories,
                    'keywords': categories,
                    'raw_data': {
                        'source': 'openalex',
                        'openalex_id': work.get('id'),
                        'fetched_at': timezone.now().isoformat()
                    }
                }
                articles.append(article)
                
            except Exception as e:
                logger.error(f"OpenAlex article parse error: {e}")
                continue
        
        return articles
    
    def _fetch_crossref(self, query: str, max_results: int) -> List[Dict]:
        """CrossRef API'den makale çek"""
        base_url = self.config.base_url or 'https://api.crossref.org/works'
        
        params = {
            'query': query,
            'rows': min(max_results, 1000),
            'sort': 'published',
            'order': 'desc'
        }
        
        response = self.session.get(base_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for item in data.get('message', {}).get('items', []):
            try:
                # Yazarlar
                authors = []
                for author in item.get('author', []):
                    name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                    authors.append({'name': name, 'orcid': author.get('ORCID', '')})
                
                # Tarih
                pub_date = None
                date_parts = item.get('published', {}).get('date-parts', [[]])
                if date_parts and date_parts[0]:
                    parts = date_parts[0]
                    if len(parts) >= 3:
                        pub_date = datetime(parts[0], parts[1], parts[2]).date()
                    elif len(parts) >= 2:
                        pub_date = datetime(parts[0], parts[1], 1).date()
                    elif len(parts) >= 1:
                        pub_date = datetime(parts[0], 1, 1).date()
                
                article = {
                    'external_id': f"crossref:{item.get('DOI', '')}",
                    'title': item.get('title', [''])[0] if item.get('title') else '',
                    'abstract': item.get('abstract', ''),
                    'authors': authors,
                    'published_date': pub_date,
                    'doi': item.get('DOI'),
                    'url': item.get('URL', ''),
                    'journal': item.get('container-title', [''])[0] if item.get('container-title') else '',
                    'volume': item.get('volume', ''),
                    'issue': item.get('issue', ''),
                    'pages': item.get('page', ''),
                    'citation_count': item.get('is-referenced-by-count', 0),
                    'categories': item.get('subject', []),
                    'keywords': item.get('subject', []),
                    'raw_data': {
                        'source': 'crossref',
                        'fetched_at': timezone.now().isoformat()
                    }
                }
                articles.append(article)
                
            except Exception as e:
                logger.error(f"CrossRef article parse error: {e}")
                continue
        
        return articles
    
    def _fetch_semantic_scholar(self, query: str, max_results: int) -> List[Dict]:
        """Semantic Scholar API'den makale çek"""
        base_url = self.config.base_url or 'https://api.semanticscholar.org/graph/v1/paper/search'
        
        params = {
            'query': query,
            'limit': min(max_results, 100),
            'fields': 'paperId,title,abstract,authors,year,citationCount,url,openAccessPdf,fieldsOfStudy,publicationDate'
        }
        
        headers = {}
        if self.config.api_key:
            headers['x-api-key'] = self.config.api_key
        
        response = self.session.get(base_url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for paper in data.get('data', []):
            try:
                # Yazarlar
                authors = [{'name': a.get('name', '')} for a in paper.get('authors', [])]
                
                # Tarih
                pub_date = None
                if paper.get('publicationDate'):
                    try:
                        pub_date = datetime.strptime(paper['publicationDate'], '%Y-%m-%d').date()
                    except:
                        pass
                elif paper.get('year'):
                    pub_date = datetime(paper['year'], 1, 1).date()
                
                # PDF
                pdf_url = ''
                if paper.get('openAccessPdf'):
                    pdf_url = paper['openAccessPdf'].get('url', '')
                
                article = {
                    'external_id': f"s2:{paper.get('paperId', '')}",
                    'title': paper.get('title', ''),
                    'abstract': paper.get('abstract', '') or '',
                    'authors': authors,
                    'published_date': pub_date,
                    'url': paper.get('url', ''),
                    'pdf_url': pdf_url,
                    'citation_count': paper.get('citationCount', 0),
                    'categories': paper.get('fieldsOfStudy', []) or [],
                    'keywords': paper.get('fieldsOfStudy', []) or [],
                    'raw_data': {
                        'source': 'semantic_scholar',
                        'paper_id': paper.get('paperId'),
                        'fetched_at': timezone.now().isoformat()
                    }
                }
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Semantic Scholar article parse error: {e}")
                continue
        
        return articles
    
    def _fetch_pubmed(self, query: str, max_results: int) -> List[Dict]:
        """PubMed API'den makale çek"""
        # İlk arama - ID'leri al
        search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'date'
        }
        
        if self.config.api_key:
            search_params['api_key'] = self.config.api_key
        
        response = self.session.get(search_url, params=search_params, timeout=60)
        response.raise_for_status()
        search_data = response.json()
        
        ids = search_data.get('esearchresult', {}).get('idlist', [])
        if not ids:
            return []
        
        # Detayları al
        fetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(ids),
            'retmode': 'xml'
        }
        
        if self.config.api_key:
            fetch_params['api_key'] = self.config.api_key
        
        response = self.session.get(fetch_url, params=fetch_params, timeout=60)
        response.raise_for_status()
        
        # XML parse
        root = ET.fromstring(response.content)
        
        articles = []
        for article_elem in root.findall('.//PubmedArticle'):
            try:
                medline = article_elem.find('.//MedlineCitation')
                article_data = medline.find('.//Article')
                
                # PMID
                pmid = medline.find('PMID').text
                
                # Title
                title = article_data.find('.//ArticleTitle').text or ''
                
                # Abstract
                abstract = ''
                abstract_elem = article_data.find('.//Abstract/AbstractText')
                if abstract_elem is not None and abstract_elem.text:
                    abstract = abstract_elem.text
                
                # Authors
                authors = []
                for author in article_data.findall('.//Author'):
                    lastname = author.find('LastName')
                    forename = author.find('ForeName')
                    if lastname is not None:
                        name = f"{forename.text if forename is not None else ''} {lastname.text}".strip()
                        authors.append({'name': name})
                
                # Journal
                journal_elem = article_data.find('.//Journal/Title')
                journal = journal_elem.text if journal_elem is not None else ''
                
                # Date
                pub_date = None
                date_elem = article_data.find('.//PubDate')
                if date_elem is not None:
                    year = date_elem.find('Year')
                    month = date_elem.find('Month')
                    day = date_elem.find('Day')
                    if year is not None:
                        y = int(year.text)
                        m = int(month.text) if month is not None and month.text.isdigit() else 1
                        d = int(day.text) if day is not None else 1
                        pub_date = datetime(y, m, d).date()
                
                # DOI
                doi = ''
                for id_elem in article_elem.findall('.//ArticleId'):
                    if id_elem.get('IdType') == 'doi':
                        doi = id_elem.text
                        break
                
                article = {
                    'external_id': f"pubmed:{pmid}",
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'published_date': pub_date,
                    'doi': doi if doi else None,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'journal': journal,
                    'categories': [],
                    'keywords': [],
                    'raw_data': {
                        'source': 'pubmed',
                        'pmid': pmid,
                        'fetched_at': timezone.now().isoformat()
                    }
                }
                articles.append(article)
                
            except Exception as e:
                logger.error(f"PubMed article parse error: {e}")
                continue
        
        return articles
    
    def _fetch_core(self, query: str, max_results: int) -> List[Dict]:
        """CORE API'den makale çek"""
        base_url = self.config.base_url or 'https://api.core.ac.uk/v3/search/works'
        
        headers = {}
        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        
        params = {
            'q': query,
            'limit': min(max_results, 100)
        }
        
        response = self.session.get(base_url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for result in data.get('results', []):
            try:
                authors = [{'name': a} for a in result.get('authors', [])]
                
                pub_date = None
                if result.get('publishedDate'):
                    try:
                        pub_date = datetime.strptime(result['publishedDate'][:10], '%Y-%m-%d').date()
                    except:
                        pass
                
                article = {
                    'external_id': f"core:{result.get('id', '')}",
                    'title': result.get('title', ''),
                    'abstract': result.get('abstract', '') or '',
                    'authors': authors,
                    'published_date': pub_date,
                    'doi': result.get('doi'),
                    'url': result.get('downloadUrl', '') or result.get('sourceFulltextUrls', [''])[0] if result.get('sourceFulltextUrls') else '',
                    'pdf_url': result.get('downloadUrl', ''),
                    'journal': result.get('publisher', ''),
                    'categories': [],
                    'keywords': [],
                    'raw_data': {
                        'source': 'core',
                        'core_id': result.get('id'),
                        'fetched_at': timezone.now().isoformat()
                    }
                }
                articles.append(article)
                
            except Exception as e:
                logger.error(f"CORE article parse error: {e}")
                continue
        
        return articles
    
    def _fetch_doaj(self, query: str, max_results: int) -> List[Dict]:
        """DOAJ API'den makale çek"""
        base_url = self.config.base_url or 'https://doaj.org/api/search/articles'
        
        params = {
            'search': query,
            'pageSize': min(max_results, 100)
        }
        
        response = self.session.get(f"{base_url}/{query}", params={'pageSize': min(max_results, 100)}, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for result in data.get('results', []):
            try:
                bibjson = result.get('bibjson', {})
                
                authors = [{'name': a.get('name', '')} for a in bibjson.get('author', [])]
                
                pub_date = None
                if bibjson.get('year'):
                    pub_date = datetime(int(bibjson['year']), 1, 1).date()
                
                article = {
                    'external_id': f"doaj:{result.get('id', '')}",
                    'title': bibjson.get('title', ''),
                    'abstract': bibjson.get('abstract', ''),
                    'authors': authors,
                    'published_date': pub_date,
                    'doi': bibjson.get('identifier', [{}])[0].get('id') if bibjson.get('identifier') else None,
                    'url': bibjson.get('link', [{}])[0].get('url', '') if bibjson.get('link') else '',
                    'journal': bibjson.get('journal', {}).get('title', ''),
                    'categories': bibjson.get('subject', []),
                    'keywords': bibjson.get('keywords', []),
                    'raw_data': {
                        'source': 'doaj',
                        'fetched_at': timezone.now().isoformat()
                    }
                }
                articles.append(article)
                
            except Exception as e:
                logger.error(f"DOAJ article parse error: {e}")
                continue
        
        return articles
    
    def _fetch_custom(self, query: str, max_results: int) -> List[Dict]:
        """Özel API için genel fetcher"""
        response = self.session.get(
            self.config.base_url,
            params={'query': query, 'limit': max_results},
            timeout=60
        )
        response.raise_for_status()
        
        # JSON varsayalım
        data = response.json()
        
        # Veri yapısına göre parse edilmeli
        # Bu kısım admin'den gelen selector/mapping'e göre düzenlenmeli
        return []


def fetch_from_source(config_id: int, query: str = None, max_results: int = None) -> Dict:
    """
    Belirli bir API kaynağından makale çek
    Admin panelinden veya API'den çağrılabilir
    """
    from ..models import APISourceConfig
    
    try:
        config = APISourceConfig.objects.get(id=config_id)
        if not config.is_active:
            return {'success': False, 'error': 'Bu kaynak aktif değil'}
        
        fetcher = APIFetcherService(config)
        return fetcher.fetch(query, max_results)
        
    except APISourceConfig.DoesNotExist:
        return {'success': False, 'error': 'Kaynak bulunamadı'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def fetch_all_active_sources() -> List[Dict]:
    """Tüm aktif kaynaklardan makale çek"""
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

