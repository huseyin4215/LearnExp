from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from .models import UserProfile, PREDEFINED_INTERESTS
from django.utils import timezone
import json


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Yeni kullanıcı kaydı"""
    try:
        data = request.data
        
        # Gerekli alanları kontrol et
        full_name = data.get('fullName', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not full_name or not email or not password:
            return Response({
                'success': False,
                'message': 'Tüm alanları doldurun.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Email zaten kayıtlı mı?
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': 'Bu e-posta adresi zaten kayıtlı.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Username olarak email kullan
        if User.objects.filter(username=email).exists():
            return Response({
                'success': False,
                'message': 'Bu e-posta adresi zaten kayıtlı.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Şifre kontrolü
        if len(password) < 6:
            return Response({
                'success': False,
                'message': 'Şifre en az 6 karakter olmalıdır.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # İsim parçala
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Kullanıcı oluştur
        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password)
        )
        
        # Boş profil oluştur
        UserProfile.objects.create(user=user)
        
        return Response({
            'success': True,
            'message': 'Hesap başarıyla oluşturuldu.',
            'user': {
                'id': user.id,
                'email': user.email,
                'fullName': f"{user.first_name} {user.last_name}".strip(),
                'isProfileComplete': False,
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Bir hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Kullanıcı girişi"""
    try:
        data = request.data
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return Response({
                'success': False,
                'message': 'E-posta ve şifre gereklidir.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Kullanıcıyı bul
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'E-posta veya şifre hatalı.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Şifre kontrolü
        user = authenticate(username=user.username, password=password)
        
        if user is None:
            return Response({
                'success': False,
                'message': 'E-posta veya şifre hatalı.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'success': False,
                'message': 'Hesabınız devre dışı bırakılmış.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Profil durumunu kontrol et
        is_profile_complete = False
        try:
            profile = user.profile
            is_profile_complete = profile.is_profile_complete
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=user)
        
        return Response({
            'success': True,
            'message': 'Giriş başarılı.',
            'user': {
                'id': user.id,
                'email': user.email,
                'fullName': f"{user.first_name} {user.last_name}".strip(),
                'isStaff': user.is_staff,
                'isProfileComplete': is_profile_complete,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Bir hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user(request, user_id):
    """Kullanıcı bilgilerini getir"""
    try:
        user = User.objects.get(id=user_id)
        
        # Profil bilgilerini al
        profile_data = {}
        try:
            profile = user.profile
            profile_data = {
                'profession': profile.profession,
                'professionDetail': profile.profession_detail,
                'companyOrInstitution': profile.company_or_institution,
                'educationLevel': profile.education_level,
                'fieldOfStudy': profile.field_of_study,
                'university': profile.university,
                'graduationYear': profile.graduation_year,
                'bio': profile.bio,
                'interests': profile.interests,
                'researchAreas': profile.research_areas,
                'website': profile.website,
                'linkedin': profile.linkedin,
                'twitter': profile.twitter,
                'orcid': profile.orcid,
                'googleScholar': profile.google_scholar,
                'isProfileComplete': profile.is_profile_complete,
                'avatarUrl': profile.avatar_url,
            }
        except UserProfile.DoesNotExist:
            pass
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'fullName': f"{user.first_name} {user.last_name}".strip(),
                'isStaff': user.is_staff,
                'dateJoined': user.date_joined,
                'profile': profile_data
            }
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kullanıcı bulunamadı.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_interests_list(request):
    """Önceden tanımlı ilgi alanları listesi"""
    return Response({
        'success': True,
        'interests': PREDEFINED_INTERESTS
    })


@api_view(['POST', 'PUT'])
@permission_classes([AllowAny])  # Prod'da IsAuthenticated yapılmalı
def update_profile(request, user_id):
    """Kullanıcı profilini güncelle (user_id ile)"""
    try:
        user = User.objects.get(id=user_id)
        return _update_user_profile(user, request.data)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kullanıcı bulunamadı.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Bir hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])  # Prod'da IsAuthenticated yapılmalı
def update_current_user_profile(request):
    """Token ile giriş yapan kullanıcının profilini güncelle"""
    try:
        # Token'dan veya request'ten user_id al
        # Şimdilik AllowAny olduğu için request body'den alıyoruz
        user_id = request.data.get('userId')
        if not user_id:
            # Header'dan almayı dene (basit token check)
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                # Gerçek JWT doğrulaması yerine basit kontrol
                # Prod'da JWT veya session authentication kullanılmalı
                pass
            
            return Response({
                'success': False,
                'message': 'Kullanıcı kimliği belirlenemedi.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = User.objects.get(id=user_id)
        return _update_user_profile(user, request.data)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kullanıcı bulunamadı.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Bir hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _update_user_profile(user, data):
    """Profil güncelleme ortak fonksiyonu"""
    # Profili al veya oluştur
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Temel bilgileri güncelle
    if 'fullName' in data:
        name_parts = data['fullName'].split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.save()
    
    # Profil alanlarını güncelle
    field_mapping = {
        'profession': 'profession',
        'professionDetail': 'profession_detail',
        'companyOrInstitution': 'company_or_institution',
        'educationLevel': 'education_level',
        'fieldOfStudy': 'field_of_study',
        'university': 'university',
        'graduationYear': 'graduation_year',
        'bio': 'bio',
        'interests': 'interests',
        'researchAreas': 'research_areas',
        'website': 'website',
        'linkedin': 'linkedin',
        'twitter': 'twitter',
        'orcid': 'orcid',
        'googleScholar': 'google_scholar',
        'avatarUrl': 'avatar_url',
    }
    
    for frontend_key, model_key in field_mapping.items():
        if frontend_key in data:
            setattr(profile, model_key, data[frontend_key])
    
    # Profil tamamlandı olarak işaretle (minimum alanlar dolduysa)
    if profile.profession and profile.field_of_study and len(profile.interests) >= 3:
        profile.is_profile_complete = True
    
    profile.save()
    
    return Response({
        'success': True,
        'message': 'Profil başarıyla güncellendi.',
        'isProfileComplete': profile.is_profile_complete
    })


# ==================== API FETCH ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_api_sources(request):
    """Tüm API kaynaklarını listele"""
    from api_collecter.models import APISourceConfig
    
    sources = APISourceConfig.objects.all().values(
        'id', 'name', 'source_type', 'is_active', 'last_fetch', 
        'total_articles_fetched', 'fetch_interval_hours'
    )
    
    return Response({
        'success': True,
        'sources': list(sources)
    })


@api_view(['POST'])
@permission_classes([AllowAny])  # Prod'da IsAuthenticated yapılmalı
def fetch_from_api_source(request, source_id):
    """Belirli bir API kaynağından makale çek"""
    from api_collecter.services.generic_fetcher import fetch_from_source
    
    query = request.data.get('query')
    max_results = request.data.get('max_results')
    
    result = fetch_from_source(source_id, query, max_results)
    
    if result.get('success'):
        return Response({
            'success': True,
            'message': f"{result.get('saved', 0)} makale eklendi, {result.get('updated', 0)} güncellendi.",
            'data': {
                'total_found': result.get('total_found', 0),
                'saved': result.get('saved', 0),
                'updated': result.get('updated', 0),
                'skipped': result.get('skipped', 0),
                'duration': result.get('duration', 0)
            }
        })
    else:
        return Response({
            'success': False,
            'message': result.get('error', 'Bilinmeyen hata')
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])  # Prod'da IsAuthenticated yapılmalı
def fetch_all_api_sources(request):
    """Tüm aktif API kaynaklarından makale çek"""
    from api_collecter.services.generic_fetcher import fetch_all_active_sources
    
    results = fetch_all_active_sources()
    
    success_count = sum(1 for r in results if r['result'].get('success'))
    total_saved = sum(r['result'].get('saved', 0) for r in results if r['result'].get('success'))
    
    return Response({
        'success': True,
        'message': f"{success_count}/{len(results)} kaynak başarılı. Toplam {total_saved} makale eklendi.",
        'results': results
    })


# ==================== SCRAPING ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_scrapers(request):
    """Tüm scraper'ları listele"""
    from webscraping.models import ScraperConfig
    
    scrapers = ScraperConfig.objects.all().values(
        'id', 'name', 'source_type', 'scraper_type', 'is_active', 
        'last_run', 'total_items_scraped', 'success_rate'
    )
    
    return Response({
        'success': True,
        'scrapers': list(scrapers)
    })


@api_view(['POST'])
@permission_classes([AllowAny])  # Prod'da IsAuthenticated yapılmalı
def run_scraper(request, scraper_id):
    """Belirli bir scraper'ı çalıştır"""
    from webscraping.services.scraper_service import scrape_from_source
    
    query = request.data.get('query')
    max_results = request.data.get('max_results')
    
    result = scrape_from_source(scraper_id, query, max_results)
    
    if result.get('success'):
        return Response({
            'success': True,
            'message': f"{result.get('saved', 0)} içerik eklendi, {result.get('updated', 0)} güncellendi.",
            'data': {
                'total_found': result.get('total_found', 0),
                'saved': result.get('saved', 0),
                'updated': result.get('updated', 0),
                'skipped': result.get('skipped', 0),
                'duration': result.get('duration', 0)
            }
        })
    else:
        return Response({
            'success': False,
            'message': result.get('error', 'Bilinmeyen hata')
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])  # Prod'da IsAuthenticated yapılmalı
def run_all_scrapers(request):
    """Tüm aktif scraper'ları çalıştır"""
    from webscraping.services.scraper_service import scrape_all_active_sources
    
    results = scrape_all_active_sources()
    
    success_count = sum(1 for r in results if r['result'].get('success'))
    total_saved = sum(r['result'].get('saved', 0) for r in results if r['result'].get('success'))
    
    return Response({
        'success': True,
        'message': f"{success_count}/{len(results)} scraper başarılı. Toplam {total_saved} içerik eklendi.",
        'results': results
    })


# ==================== ARTICLES ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_articles(request):
    """Makaleleri listele - Gelişmiş filtreleme ve pagination"""
    from api_collecter.models import Article
    from django.db.models import Q
    from datetime import datetime, timedelta
    
    # Query parameters
    search = request.query_params.get('search', '').strip()
    categories = request.query_params.get('categories', '').strip()
    source = request.query_params.get('source', '').strip()
    date_from = request.query_params.get('date_from', '').strip()
    date_to = request.query_params.get('date_to', '').strip()
    date_range = request.query_params.get('date_range', '').strip()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    
    # Base queryset
    queryset = Article.objects.select_related('api_source').all().order_by('-published_date', '-fetched_at')
    
    # Search filter
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | 
            Q(abstract__icontains=search) |
            Q(authors__icontains=search) |
            Q(keywords__icontains=search)
        )
    
    # Categories filter
    if categories:
        category_list = [c.strip() for c in categories.split(',')]
        q_objects = Q()
        for category in category_list:
            q_objects |= Q(categories__icontains=category)
        queryset = queryset.filter(q_objects)
    
    # Source filter
    if source:
        try:
            source_id = int(source)
            queryset = queryset.filter(api_source_id=source_id)
        except ValueError:
            queryset = queryset.filter(api_source__name__icontains=source)
    
    # Date range filter
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(published_date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(published_date__lte=to_date)
        except ValueError:
            pass
    
    # Quick date filters
    if date_range:
        today = datetime.now().date()
        if date_range == 'last_30_days':
            queryset = queryset.filter(published_date__gte=today - timedelta(days=30))
        elif date_range == 'last_3_months':
            queryset = queryset.filter(published_date__gte=today - timedelta(days=90))
        elif date_range == 'last_year':
            queryset = queryset.filter(published_date__gte=today - timedelta(days=365))
    
    # Count total
    total = queryset.count()
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    articles = queryset[start:end]
    
    # Serialize
    results = []
    for article in articles:
        results.append({
            'id': article.id,
            'external_id': article.external_id,
            'title': article.title,
            'abstract': article.abstract,
            'authors': article.authors,
            'published_date': article.published_date.isoformat() if article.published_date else None,
            'journal': article.journal,
            'volume': article.volume,
            'issue': article.issue,
            'pages': article.pages,
            'url': article.url,
            'pdf_url': article.pdf_url,
            'image_url': getattr(article, 'image_url', ''),
            'doi': article.doi,
            'categories': article.categories,
            'keywords': article.keywords,
            'citation_count': article.citation_count,
            'api_source': {
                'id': article.api_source.id,
                'name': article.api_source.name,
            } if article.api_source else None,
            'fetched_at': article.fetched_at.isoformat(),
        })
    
    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1
    
    return Response({
        'count': total,
        'next': f'?page={page + 1}' if has_next else None,
        'previous': f'?page={page - 1}' if has_previous else None,
        'total_pages': total_pages,
        'current_page': page,
        'page_size': page_size,
        'results': results
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_article(request, article_id):
    """Tek makale detayı"""
    from api_collecter.models import Article
    
    try:
        article = Article.objects.get(id=article_id)
        return Response({
            'success': True,
            'article': {
                'id': article.id,
                'title': article.title,
                'abstract': article.abstract,
                'authors': article.authors,
                'published_date': article.published_date,
                'journal': article.journal,
                'volume': article.volume,
                'issue': article.issue,
                'pages': article.pages,
                'doi': article.doi,
                'url': article.url,
                'pdf_url': article.pdf_url,
                'image_url': getattr(article, 'image_url', ''),
                'categories': article.categories,
                'keywords': article.keywords,
                'citation_count': article.citation_count,
                'fetched_at': article.fetched_at,
            }
        })
    except Article.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Makale bulunamadı.'
        }, status=status.HTTP_404_NOT_FOUND)


# ==================== API SOURCES ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_api_sources_list(request):
    """API kaynaklarını listele"""
    from api_collecter.models import APISourceConfig
    
    sources = APISourceConfig.objects.filter(is_active=True).values(
        'id', 'name', 'description', 'response_format', 'total_articles_fetched'
    )
    
    return Response({
        'count': sources.count(),
        'results': list(sources)
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def search_live_from_apis(request):
    """
    Canlı API + Scraper araması - Kullanıcı arama yaptığında tüm aktif API'lerden
    ve seçili scraper'lardan anlık arama yapar. Sources are fetched in parallel.
    """
    from api_collecter.models import APISourceConfig
    from api_collecter.services.generic_fetcher import GenericAPIFetcher
    from webscraping.models import ScraperConfig
    from webscraping.services.scraper_orchestrator import ScraperOrchestrator
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    search_query = request.data.get('query', '').strip()
    max_results = int(request.data.get('max_results', 20))
    source_ids = request.data.get('source_ids', [])  # API kaynak ID'leri
    scraper_ids = request.data.get('scraper_ids', [])  # Scraper kaynak ID'leri
    
    if not search_query:
        return Response({
            'success': False,
            'message': 'Arama sorgusu gerekli'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    has_api_sources = bool(source_ids)
    has_scraper_sources = bool(scraper_ids)
    
    if not has_api_sources and not has_scraper_sources:
        has_api_sources = True
    
    articles_by_source = {}
    errors = []
    sources_searched = 0
    
    import re
    today = timezone.now().date()
    
    # ==================== HELPER FUNCTIONS ====================
    
    def _clean_api_article(article_data, source_name):
        """Clean and normalize a single API article"""
        title = article_data.get('title', '').strip()
        if not title:
            return None
        
        pub_date = article_data.get('published_date')
        pub_date_str = ''
        if pub_date is not None:
            pub_date_str = str(pub_date)
            if pub_date_str in ('None', ''):
                pub_date_str = ''
        
        if pub_date_str:
            try:
                from datetime import datetime as dt
                parsed_date = dt.strptime(pub_date_str[:10], '%Y-%m-%d').date()
                if parsed_date > today:
                    return None
            except (ValueError, TypeError):
                pass
        
        authors = article_data.get('authors', [])
        if isinstance(authors, list):
            authors = [a for a in authors if isinstance(a, dict) and a.get('name', '').strip()]
        
        url = article_data.get('url', '') or ''
        doi = article_data.get('doi', '') or ''
        external_id = article_data.get('external_id', '') or ''
        
        if not url and doi:
            clean_doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
            url = f'https://doi.org/{clean_doi}'
        elif not url and external_id:
            if external_id.startswith('http'):
                url = external_id
        
        if not url:
            return None
        
        abstract = article_data.get('abstract', '') or ''
        keywords = article_data.get('keywords', []) or []
        
        kw_match = re.search(r'keywords?\s*:\s*(.+?)(?:\.|$)', abstract, re.IGNORECASE)
        if kw_match:
            extracted_kw = [k.strip() for k in kw_match.group(1).split(',') if k.strip()]
            if extracted_kw:
                keywords = list(set(keywords + extracted_kw))
            abstract = re.sub(r'\s*keywords?\s*:\s*.+?(?:\.|$)', '', abstract, flags=re.IGNORECASE).strip()
        
        if len(abstract) > 1500:
            abstract = abstract[:1500].rsplit(' ', 1)[0] + '...'
        
        return {
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'published_date': pub_date_str,
            'journal': article_data.get('journal', '') or '',
            'url': url,
            'pdf_url': article_data.get('pdf_url', '') or '',
            'image_url': article_data.get('image_url', '') or '',
            'doi': doi,
            'categories': article_data.get('categories', []) or [],
            'keywords': keywords,
            'citation_count': article_data.get('citation_count', 0) or 0,
            'source': source_name,
            'external_id': external_id,
        }
    
    def _fetch_from_api_source(source):
        """Fetch articles from a single API source (runs in thread)"""
        try:
            fetcher = GenericAPIFetcher(source)
            result = fetcher.fetch(search_query, max_results)
            
            if result['success']:
                source_articles = []
                for article_data in result.get('articles', []):
                    cleaned = _clean_api_article(article_data, source.name)
                    if cleaned:
                        source_articles.append(cleaned)
                return {'source': source.name, 'articles': source_articles, 'error': None}
            else:
                return {'source': source.name, 'articles': [], 'error': result.get('error', 'Unknown error')}
        except Exception as e:
            return {'source': source.name, 'articles': [], 'error': str(e)}
    
    def _fetch_from_scraper_source(config):
        """Fetch articles from a single scraper source (runs in thread)"""
        try:
            orchestrator = ScraperOrchestrator(config)
            result = orchestrator.scrape(
                query=search_query,
                max_results=max_results,
                triggered_by='api'
            )
            
            if result.get('success'):
                scraper_articles = []
                for item in result.get('items', []):
                    title = (item.title or '').strip()
                    if not title:
                        continue
                    
                    authors = item.authors or []
                    if isinstance(authors, list):
                        authors = [
                            a if isinstance(a, dict) else {'name': str(a)}
                            for a in authors if a
                        ]
                    
                    pub_date_str = ''
                    if item.published_date is not None:
                        pub_date_str = str(item.published_date)
                        if pub_date_str in ('None', ''):
                            pub_date_str = ''
                    
                    url = item.url or ''
                    if not url:
                        continue
                    
                    abstract = item.abstract or ''
                    if len(abstract) > 1500:
                        abstract = abstract[:1500].rsplit(' ', 1)[0] + '...'
                    
                    scraper_articles.append({
                        'title': title,
                        'abstract': abstract,
                        'authors': authors,
                        'published_date': pub_date_str,
                        'journal': item.journal or '',
                        'url': url,
                        'pdf_url': item.pdf_url or '',
                        'image_url': item.image_url or '',
                        'doi': item.doi or '',
                        'categories': item.categories or [],
                        'keywords': item.keywords or [],
                        'citation_count': 0,
                        'source': config.name,
                        'external_id': item.external_id or '',
                    })
                return {'source': config.name, 'articles': scraper_articles, 'error': None}
            else:
                return {'source': config.name, 'articles': [], 'error': result.get('error', 'Scraping başarısız')}
        except Exception as e:
            return {'source': config.name, 'articles': [], 'error': str(e)}
    
    # ==================== PARALLEL FETCH ====================
    
    futures = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        # Submit API source tasks
        if has_api_sources:
            if source_ids:
                api_sources = APISourceConfig.objects.filter(id__in=source_ids, is_active=True)
            else:
                api_sources = APISourceConfig.objects.filter(is_active=True)
            
            sources_searched += api_sources.count()
            for source in api_sources:
                futures.append(executor.submit(_fetch_from_api_source, source))
        
        # Submit scraper source tasks
        if has_scraper_sources and scraper_ids:
            scraper_configs = ScraperConfig.objects.filter(id__in=scraper_ids, is_active=True)
            sources_searched += scraper_configs.count()
            for config in scraper_configs:
                futures.append(executor.submit(_fetch_from_scraper_source, config))
        
        # Collect results with timeout
        for future in as_completed(futures, timeout=120):
            try:
                result = future.result(timeout=60)
                if result['articles']:
                    articles_by_source[result['source']] = result['articles']
                if result['error']:
                    errors.append({'source': result['source'], 'error': result['error']})
            except Exception as e:
                errors.append({'source': 'unknown', 'error': f'Task error: {str(e)}'})
    
    # ==================== SONUÇLARI BİRLEŞTİR ====================
    if not articles_by_source and not errors:
        return Response({
            'success': False,
            'message': 'Aktif kaynak bulunamadı'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Interleave articles from different sources (round-robin)
    interleaved = []
    source_lists = list(articles_by_source.values())
    if source_lists:
        max_len = max(len(lst) for lst in source_lists)
        for i in range(max_len):
            for lst in source_lists:
                if i < len(lst):
                    interleaved.append(lst[i])
    
    # DEDUPLICATION: by DOI first, then external_id
    seen_ids = set()
    unique_articles = []
    for article in interleaved:
        dedup_key = article.get('doi') or article.get('external_id') or article.get('title', '')
        if dedup_key and dedup_key not in seen_ids:
            seen_ids.add(dedup_key)
            unique_articles.append(article)
    
    return Response({
        'success': True,
        'query': search_query,
        'total_found': len(unique_articles),
        'sources_searched': sources_searched,
        'articles': unique_articles[:max_results],
        'errors': errors if errors else None
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories_list(request):
    """Tüm kategorileri listele"""
    from api_collecter.models import Article
    from django.db.models import Count
    
    # Get all unique categories from articles
    articles = Article.objects.exclude(categories=[]).values_list('categories', flat=True)
    
    # Flatten and count categories
    category_counts = {}
    for categories_list in articles:
        for category in categories_list:
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
    
    # Sort by count
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    return Response({
        'categories': [cat[0] for cat in sorted_categories[:50]],  # Top 50
        'category_counts': dict(sorted_categories[:50])
    })


# ==================== SCRAPED CONTENT ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_scraped_contents(request):
    """Scrape edilen içerikleri listele"""
    from webscraping.models import ScrapedContent
    
    page = int(request.query_params.get('page', 1))
    per_page = int(request.query_params.get('per_page', 20))
    search = request.query_params.get('search', '')
    content_type = request.query_params.get('content_type', '')
    
    queryset = ScrapedContent.objects.select_related('scraper_config').all()
    
    if search:
        queryset = queryset.filter(title__icontains=search) | queryset.filter(abstract__icontains=search)
    
    if content_type:
        queryset = queryset.filter(content_type=content_type)
    
    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    contents = []
    for item in queryset[start:end]:
        contents.append({
            'id': item.id,
            'title': item.title,
            'abstract': item.abstract,
            'content_type': item.content_type,
            'authors': item.authors,
            'published_date': item.published_date.isoformat() if item.published_date else None,
            'source_url': item.source_url,
            'keywords': item.keywords,
            'image_url': item.image_url,
            'scraper_name': item.scraper_config.name if item.scraper_config else None,
        })
    
    return Response({
        'success': True,
        'total': total,
        'page': page,
        'per_page': per_page,
        'contents': contents
    })


# ============================================================================
# LIBRARY (Kullanıcı Kütüphanesi)
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def library_list(request):
    """Kullanıcının kaydedilen makalelerini listele"""
    from .models import SavedArticle
    
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({'success': False, 'message': 'user_id gerekli'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    search = request.query_params.get('search', '').strip()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    
    queryset = SavedArticle.objects.filter(user_id=user_id)
    
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(title__icontains=search) | 
            Q(abstract__icontains=search)
        )
    
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = queryset[start:end]
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    results = []
    for item in items:
        results.append({
            'id': item.id,
            'external_id': item.external_id,
            'title': item.title,
            'abstract': item.abstract,
            'authors': item.authors,
            'published_date': item.published_date,
            'journal': item.journal,
            'url': item.url,
            'pdf_url': item.pdf_url,
            'doi': item.doi,
            'source': item.source_name,
            'categories': item.categories,
            'citation_count': item.citation_count,
            'saved_at': item.saved_at.isoformat(),
        })
    
    return Response({
        'success': True,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'items': results
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def library_save(request):
    """Makaleyi kullanıcının kütüphanesine kaydet"""
    from .models import SavedArticle
    from django.contrib.auth.models import User
    
    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'success': False, 'message': 'user_id gerekli'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'Kullanıcı bulunamadı'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    external_id = request.data.get('external_id', '')
    if not external_id:
        return Response({'success': False, 'message': 'external_id gerekli'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Check if already saved (duplicate prevention)
    if SavedArticle.objects.filter(user=user, external_id=external_id).exists():
        return Response({
            'success': True, 
            'message': 'Bu makale zaten kütüphanenizde',
            'already_saved': True
        })
    
    saved = SavedArticle.objects.create(
        user=user,
        external_id=external_id,
        title=request.data.get('title', ''),
        abstract=request.data.get('abstract', ''),
        authors=request.data.get('authors', []),
        published_date=request.data.get('published_date', ''),
        journal=request.data.get('journal', ''),
        url=request.data.get('url', ''),
        pdf_url=request.data.get('pdf_url', ''),
        doi=request.data.get('doi', ''),
        source_name=request.data.get('source', ''),
        categories=request.data.get('categories', []),
        citation_count=request.data.get('citation_count', 0),
    )
    
    return Response({
        'success': True,
        'message': 'Makale kütüphaneye kaydedildi',
        'saved_id': saved.id
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def library_remove(request):
    """Makaleyi kullanıcının kütüphanesinden kaldır"""
    from .models import SavedArticle
    
    user_id = request.data.get('user_id')
    external_id = request.data.get('external_id', '')
    
    if not user_id or not external_id:
        return Response({'success': False, 'message': 'user_id ve external_id gerekli'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    deleted, _ = SavedArticle.objects.filter(
        user_id=user_id, external_id=external_id
    ).delete()
    
    return Response({
        'success': True,
        'message': 'Makale kütüphaneden kaldırıldı' if deleted else 'Makale bulunamadı',
        'removed': deleted > 0
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def library_check(request):
    """Hangi makalelerin kaydedilmiş olduğunu kontrol et"""
    from .models import SavedArticle
    
    user_id = request.data.get('user_id')
    external_ids = request.data.get('external_ids', [])
    
    if not user_id:
        return Response({'success': False, 'message': 'user_id gerekli'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    saved_ids = list(SavedArticle.objects.filter(
        user_id=user_id, 
        external_id__in=external_ids
    ).values_list('external_id', flat=True))
    
    return Response({
        'success': True,
        'saved_ids': saved_ids
    })
