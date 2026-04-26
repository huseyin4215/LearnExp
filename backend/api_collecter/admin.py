"""
Veri Toplama Admin Paneli - Basitleştirilmiş
API ve Web Scraping yönetimi
"""
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils import timezone

# API Collecter modelleri
from .models import APISourceConfig, APIFetchLog, Article

# Web Scraping orijinal modelleri (admin'den kaldırmak için)
from webscraping.models import ScraperConfig, ScrapeLog, ScrapedContent, ProxyConfig

# Proxy modeller (api_collecter altında görünmesi için)
from .proxy_models import ScraperKonfig, ScrapeLogu, ScrapeIcerik


# ============================================================================
# Webscraping orijinal modellerini admin'den kaldır (eğer kayıtlıysa)
# ============================================================================
try:
    admin.site.unregister(ScraperConfig)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(ScrapeLog)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(ScrapedContent)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(ProxyConfig)
except admin.sites.NotRegistered:
    pass


# ============================================================================
# API KAYNAK KONFİGÜRASYONLARI
# ============================================================================

@admin.register(APISourceConfig)
class APISourceConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'response_format', 'is_active', 'status_badge', 'fetch_interval_hours', 
                    'last_fetch', 'total_articles_fetched', 'next_fetch']
    list_filter = ['response_format', 'auth_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'base_url', 'default_search_query']
    readonly_fields = ['created_at', 'updated_at', 'last_fetch', 'next_fetch', 'total_articles_fetched', 
                       'total_requests_made', 'last_error', 'last_error_at']
    list_editable = ['is_active']
    ordering = ['-is_active', 'name']
    
    fieldsets = (
        ('🔧 Temel Bilgiler', {
            'fields': ('name', 'description', 'is_active'),
            'description': 'API kaynağının temel bilgileri'
        }),
        ('🔗 Bağlantı Ayarları', {
            'fields': ('base_url', 'http_method', 'response_format', 'timeout_seconds', 'verify_ssl'),
            'description': 'API endpoint ve format ayarları'
        }),
        ('🔐 Kimlik Doğrulama', {
            'fields': ('auth_type', 'api_key', 'api_key_header_name', 'api_key_param_name', 'api_secret'),
            'classes': ('collapse',),
            'description': 'API kimlik doğrulama ayarları'
        }),
        ('📤 İstek Parametreleri', {
            'fields': ('query_params', 'request_body_template', 'custom_headers'),
            'classes': ('collapse',),
            'description': 'Dinamik sorgu parametreleri ve headers (JSON formatında)'
        }),
        ('🔍 Arama Ayarları', {
            'fields': ('default_search_query', 'categories', 'max_results_per_request'),
            'description': 'Varsayılan arama ayarları'
        }),
        ('📥 Yanıt Parse Ayarları', {
            'fields': ('response_data_path', 'field_mappings', 'date_format', 
                      'author_field_type', 'author_name_field'),
            'classes': ('collapse',),
            'description': 'API yanıtını parse etme kuralları'
        }),
        ('⏱️ Rate Limiting', {
            'fields': ('rate_limit_per_minute', 'rate_limit_per_hour', 'request_delay_seconds'),
            'description': 'İstek hızı sınırlamaları'
        }),
        ('⏰ Zamanlama', {
            'fields': ('fetch_interval_hours', 'last_fetch', 'next_fetch'),
            'description': 'Otomatik çekme zamanlaması'
        }),
        ('🔄 Pagination', {
            'fields': ('supports_pagination', 'pagination_param_name', 'pagination_start'),
            'classes': ('collapse',),
        }),
        ('📊 İstatistikler', {
            'fields': ('total_articles_fetched', 'total_requests_made', 'last_error', 'last_error_at'),
            'classes': ('collapse',)
        }),
        ('📅 Sistem', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span style="background:#10b981;color:white;padding:3px 10px;border-radius:12px;font-size:11px;">✓ Aktif</span>')
        return mark_safe('<span style="background:#ef4444;color:white;padding:3px 10px;border-radius:12px;font-size:11px;">✗ Pasif</span>')
    status_badge.short_description = 'Durum'
    
    actions = ['activate_sources', 'deactivate_sources', 'fetch_now']
    
    @admin.action(description="✅ Seçili kaynakları aktif et")
    def activate_sources(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} kaynak aktif edildi.")
    
    @admin.action(description="❌ Seçili kaynakları pasif et")
    def deactivate_sources(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} kaynak pasif edildi.")
    
    @admin.action(description="🚀 Seçili kaynaklardan şimdi veri çek")
    def fetch_now(self, request, queryset):
        from .services.generic_fetcher import fetch_from_source
        
        success_count = 0
        error_count = 0
        total_articles = 0
        
        for config in queryset:
            result = fetch_from_source(config.id)
            if result.get('success'):
                success_count += 1
                total_articles += result.get('saved', 0)
            else:
                error_count += 1
        
        if error_count > 0:
            self.message_user(request, f"⚠️ {success_count} başarılı, {error_count} başarısız. Toplam {total_articles} makale.", level='warning')
        else:
            self.message_user(request, f"✅ {success_count} kaynaktan {total_articles} makale çekildi.")


# ============================================================================
# SCRAPER KONFİGÜRASYONLARI (Proxy Model)
# ============================================================================

@admin.register(ScraperKonfig)
class ScraperKonfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'scraper_type', 'is_active', 'status_badge', 
                    'scrape_interval_hours', 'last_run', 'total_items_scraped', 'success_rate_display']
    list_filter = ['source_type', 'scraper_type', 'is_active', 'created_at']
    search_fields = ['name', 'search_query', 'base_url']
    readonly_fields = ['created_at', 'updated_at', 'last_run', 'next_run', 'total_items_scraped', 'success_rate']
    list_editable = ['is_active']
    ordering = ['-is_active', 'name']
    
    # Custom template to add buttons and preview
    change_form_template = 'admin/api_collecter/scraperkonfig/change_form.html'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/test-scrape/', self.admin_site.admin_view(self.test_scrape_view), name='scraper_test_scrape'),
            path('auto-config/', self.admin_site.admin_view(self.auto_config_view), name='scraper_auto_config'),
        ]
        return custom_urls + urls

    def test_scrape_view(self, request, object_id):
        from django.http import JsonResponse
        from webscraping.services.scraper_orchestrator import ScraperOrchestrator
        
        config = self.get_object(request, object_id)
        if not config:
            return JsonResponse({'success': False, 'error': 'Config not found'})
            
        try:
            # For testing, we might want to use unsaved form data
            # But here we use the stored object for simplicity first
            orchestrator = ScraperOrchestrator(config)
            # Run in test mode (no save, returns first 10 items)
            result = orchestrator.scrape(triggered_by='admin_test', test_mode=True)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def auto_config_view(self, request):
        from django.http import JsonResponse
        from webscraping.services.auto_config_service import AutoConfigService
        from django.views.decorators.http import require_POST
        
        # We can use GET or POST here for flexibility in the admin
        url = request.POST.get('url') or request.GET.get('url')
        
        if not url:
            return JsonResponse({'success': False, 'error': 'URL is required'})
            
        try:
            service = AutoConfigService(url)
            result = service.detect_selectors()
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    fieldsets = (
        ('🔧 Temel Ayarlar', {
            'fields': ('name', 'source_type', 'scraper_type', 'content_category', 'is_active'),
            'description': (
                'scraper_type: "html" = requests+BeautifulSoup (static pages only), '
                '"selenium" = browser automation (JavaScript/SPA pages), '
                '"rss" = RSS/Atom feeds'
            )
        }),
        ('🌐 URL ve Bağlantı', {
            'fields': ('base_url', 'verify_ssl'),
        }),
        ('🔐 Giriş (Login)', {
            'fields': ('requires_login', 'login_url', 'username', 'password',
                       'login_username_field', 'login_password_field'),
            'classes': ('collapse',),
            'description': 'Oturum açma gerektiren siteler için'
        }),
        ('🔍 Arama ve Filtreleme', {
            'fields': ('search_query', 'categories', 'date_filter_start', 'date_filter_end'),
        }),
        ('⚙️ Scraping Ayarları', {
            'fields': (
                'max_results', 'max_pages', 'delay_between_requests', 
                'delay_between_pages', 'timeout_seconds', 'use_sibling_payload', 
                'max_results_per_request'
            ),
        }),
        ('🚀 Advanced Crawling (Multi-Stage)', {
            'fields': (
                'enable_multi_step', 'enable_query_encoding', 'enable_relative_url_fix',
                'max_depth', 'max_pages_per_step',
                'enable_infinite_scroll', 'scroll_count', 'scroll_delay'
            ),
            'description': 'Çok aşamalı tarama ve dinamik içerik (Infinite Scroll) ayarları.'
        }),
        ('🎯 Stage 1 Selectors (Discovery)', {
            'fields': ('step1_selectors',),
            'classes': ('collapse',),
            'description': 'İlk aşamada toplanacak URL/Link seçicileri.'
        }),
        ('🎯 Stage 2 Selectors (Extraction)', {
            'fields': ('step2_selectors',),
            'classes': ('collapse',),
            'description': 'İkinci aşamada detay sayfalarından toplanacak veri seçicileri.'
        }),
        ('📄 Sayfalama (Pagination)', {
            'fields': ('pagination_type', 'pagination_template', 'pagination_url_pattern',
                       'pagination_start_page', 'stop_when_empty'),
            'description': (
                'url_increment: {page} placeholder ile URL şablonu kullanır. '
                'Örnek: https://site.com/haberler/{page}'
            )
        }),
        ('🎯 CSS/XPath Seçiciler', {
            'fields': ('selector_type', 'selectors', 'date_format'),
            'description': (
                'JSON formatında seçiciler. Zorunlu alanlar:\n'
                '• item_container: Öğe kapsayıcı seçici (örn: ".card", "article")\n'
                '• title: Başlık seçici\n'
                '• url: Link seçici (href alınır)\n'
                'İsteğe bağlı: abstract, image, published_date, authors, categories, '
                'pagination_next\n\n'
                'Örnek: {"item_container": ".card", "title": ".card-title a", '
                '"url": ".card-title a", "image": ".card-img-top", '
                '"published_date": ".card-text span"}'
            )
        }),
        ('📡 HTTP Ayarları', {
            'fields': ('user_agent', 'custom_headers', 'cookies'),
            'classes': ('collapse',)
        }),
        ('⏰ Zamanlama', {
            'fields': ('scrape_interval_hours', 'last_run', 'next_run'),
        }),
        ('📊 İstatistikler', {
            'fields': ('total_items_scraped', 'success_rate'),
            'classes': ('collapse',)
        }),
        ('📅 Sistem', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span style="background:#10b981;color:white;padding:3px 10px;border-radius:12px;font-size:11px;">✓ Aktif</span>')
        return mark_safe('<span style="background:#ef4444;color:white;padding:3px 10px;border-radius:12px;font-size:11px;">✗ Pasif</span>')
    status_badge.short_description = 'Durum'
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        if rate >= 90:
            color = '#10b981'
        elif rate >= 70:
            color = '#f59e0b'
        else:
            color = '#ef4444'
        return mark_safe(f'<span style="color:{color};font-weight:bold;">%{rate:.0f}</span>')
    success_rate_display.short_description = 'Başarı'
    
    actions = ['activate_scrapers', 'deactivate_scrapers', 'run_scrapers_now']
    
    @admin.action(description="✅ Seçili scraper'ları aktif et")
    def activate_scrapers(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} scraper aktif edildi.")
    
    @admin.action(description="❌ Seçili scraper'ları pasif et")
    def deactivate_scrapers(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} scraper pasif edildi.")
    
    @admin.action(description="🚀 Seçili scraper'ları şimdi çalıştır")
    def run_scrapers_now(self, request, queryset):
        from webscraping.services.scraper_orchestrator import ScraperOrchestrator
        
        success_count = 0
        error_count = 0
        total_items = 0
        errors_detail = []
        
        for config in queryset:
            try:
                orchestrator = ScraperOrchestrator(config)
                result = orchestrator.scrape(triggered_by='manual')
                if result.get('success'):
                    success_count += 1
                    total_items += result.get('saved', 0)
                else:
                    error_count += 1
                    errors_detail.append(f"{config.name}: {result.get('error', 'Unknown')}")
            except Exception as e:
                error_count += 1
                errors_detail.append(f"{config.name}: {str(e)}")
        
        if error_count > 0:
            detail = "; ".join(errors_detail[:3])
            self.message_user(
                request, 
                f"⚠️ {success_count} başarılı, {error_count} başarısız. "
                f"Toplam {total_items} içerik. Hatalar: {detail}", 
                level='warning'
            )
        else:
            self.message_user(request, f"✅ {success_count} scraper'dan {total_items} içerik çekildi.")


# ============================================================================
# İÇERİK YÖNETİMİ - MAKALELER (saved_data uygulamasına taşındı)
# ============================================================================


# ============================================================================
# İÇERİK YÖNETİMİ - SCRAPE EDİLEN İÇERİKLER (saved_data uygulamasına taşındı)
# ============================================================================


# ============================================================================
# LOGLAR - API FETCH
# ============================================================================

@admin.register(APIFetchLog)
class APIFetchLogAdmin(admin.ModelAdmin):
    list_display = ['api_config', 'status_badge', 'articles_found', 'articles_saved', 
                    'duration_display', 'started_at']
    list_filter = ['status', 'api_config', 'started_at']
    search_fields = ['api_config__name', 'error_message']
    readonly_fields = ['api_config', 'status', 'request_url', 'request_params', 'articles_found', 
                       'articles_saved', 'articles_updated', 'articles_skipped', 'error_message', 
                       'error_details', 'started_at', 'completed_at', 'duration_seconds']
    date_hierarchy = 'started_at'
    ordering = ['-started_at']
    
    fieldsets = (
        ('📋 Genel Bilgi', {
            'fields': ('api_config', 'status')
        }),
        ('📤 İstek Detayları', {
            'fields': ('request_url', 'request_params'),
            'classes': ('collapse',)
        }),
        ('📊 Sonuçlar', {
            'fields': ('articles_found', 'articles_saved', 'articles_updated', 'articles_skipped')
        }),
        ('⚠️ Hata Bilgileri', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
        ('⏱️ Zamanlama', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'started': '#3b82f6',
            'fetching': '#f59e0b',
            'processing': '#8b5cf6',
            'success': '#10b981',
            'partial': '#84cc16',
            'failed': '#ef4444',
            'cancelled': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return mark_safe(f'<span style="color:{color};font-weight:bold;">{obj.get_status_display()}</span>')
    status_badge.short_description = 'Durum'
    
    def duration_display(self, obj):
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.1f}s"
            return f"{obj.duration_seconds/60:.1f}m"
        return "-"
    duration_display.short_description = 'Süre'


# ============================================================================
# LOGLAR - SCRAPE (Proxy Model)
# ============================================================================

@admin.register(ScrapeLogu)
class ScrapeLoguAdmin(admin.ModelAdmin):
    list_display = ['scraper_config', 'status_badge', 'items_found', 'items_saved', 
                    'items_failed', 'duration_display', 'triggered_by', 'started_at']
    list_filter = ['status', 'scraper_config', 'triggered_by', 'started_at']
    search_fields = ['scraper_config__name', 'error_message', 'notes']
    readonly_fields = ['scraper_config', 'status', 'pages_scraped', 'items_found', 'items_saved',
                       'items_updated', 'items_skipped', 'items_failed', 'error_message', 'error_traceback',
                       'failed_urls', 'requests_made', 'bytes_downloaded', 'started_at', 'completed_at',
                       'duration_seconds', 'triggered_by']
    date_hierarchy = 'started_at'
    ordering = ['-started_at']
    
    fieldsets = (
        ('📋 Genel Bilgi', {
            'fields': ('scraper_config', 'status', 'triggered_by')
        }),
        ('📊 Sonuçlar', {
            'fields': ('pages_scraped', 'items_found', 'items_saved', 'items_updated', 'items_skipped', 'items_failed')
        }),
        ('⚡ Performans', {
            'fields': ('requests_made', 'bytes_downloaded', 'duration_seconds'),
            'classes': ('collapse',)
        }),
        ('⚠️ Hatalar', {
            'fields': ('error_message', 'error_traceback', 'failed_urls'),
            'classes': ('collapse',)
        }),
        ('⏱️ Zamanlama', {
            'fields': ('started_at', 'completed_at')
        }),
        ('📝 Notlar', {
            'fields': ('notes',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'queued': '#6b7280',
            'started': '#3b82f6',
            'running': '#f59e0b',
            'success': '#10b981',
            'partial': '#84cc16',
            'failed': '#ef4444',
            'timeout': '#8b5cf6',
            'cancelled': '#6b7280',
        }
        icons = {
            'queued': '⏳',
            'started': '🚀',
            'running': '⚡',
            'success': '✓',
            'partial': '⚠',
            'failed': '✗',
            'timeout': '⏰',
            'cancelled': '🚫',
        }
        color = colors.get(obj.status, '#6b7280')
        icon = icons.get(obj.status, '')
        return mark_safe(f'<span style="color:{color};font-weight:bold;">{icon} {obj.get_status_display()}</span>')
    status_badge.short_description = 'Durum'
    
    def duration_display(self, obj):
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.1f}s"
            elif obj.duration_seconds < 3600:
                return f"{obj.duration_seconds/60:.1f}m"
            return f"{obj.duration_seconds/3600:.1f}h"
        return "-"
    duration_display.short_description = 'Süre'


