from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ScraperConfig, ScrapeLog, ScrapedContent, ProxyConfig


@admin.register(ScraperConfig)
class ScraperConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'scraper_type', 'is_active_display', 'scrape_interval_hours', 
                    'last_run', 'total_items_scraped', 'success_rate_display']
    list_filter = ['source_type', 'scraper_type', 'is_active', 'created_at']
    search_fields = ['name', 'search_query', 'base_url']
    readonly_fields = ['created_at', 'updated_at', 'last_run', 'next_run', 'total_items_scraped', 'success_rate']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'source_type', 'scraper_type', 'is_active')
        }),
        ('URL ve Bağlantı', {
            'fields': ('base_url', 'login_url', 'username', 'password')
        }),
        ('Arama Ayarları', {
            'fields': ('search_query', 'categories', 'date_filter_start', 'date_filter_end')
        }),
        ('Scraping Ayarları', {
            'fields': ('max_results', 'max_pages', 'delay_between_requests', 'timeout_seconds')
        }),
        ('HTTP Ayarları', {
            'fields': ('user_agent', 'custom_headers'),
            'classes': ('collapse',)
        }),
        ('Seçiciler (HTML Parsing)', {
            'fields': ('selectors',),
            'classes': ('collapse',),
            'description': 'CSS/XPath seçicileri JSON formatında'
        }),
        ('Zamanlama', {
            'fields': ('scrape_interval_hours', 'last_run', 'next_run')
        }),
        ('İstatistikler', {
            'fields': ('total_items_scraped', 'success_rate'),
            'classes': ('collapse',)
        }),
        ('Sistem', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Aktif</span>')
        return format_html('<span style="color: red;">✗ Pasif</span>')
    is_active_display.short_description = 'Durum'
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        return format_html(f'<span style="color: {color};">%{rate:.1f}</span>')
    success_rate_display.short_description = 'Başarı'
    
    actions = ['activate_scrapers', 'deactivate_scrapers', 'run_scrapers_now']
    
    def activate_scrapers(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} scraper aktif edildi.")
    activate_scrapers.short_description = "Seçili scraper'ları aktif et"
    
    def deactivate_scrapers(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} scraper pasif edildi.")
    deactivate_scrapers.short_description = "Seçili scraper'ları pasif et"
    
    def run_scrapers_now(self, request, queryset):
        # TODO: Celery task tetikle
        self.message_user(request, f"{queryset.count()} scraper çalıştırılmak üzere kuyruğa eklendi.")
    run_scrapers_now.short_description = "Seçili scraper'ları şimdi çalıştır"


@admin.register(ScrapeLog)
class ScrapeLogAdmin(admin.ModelAdmin):
    list_display = ['scraper_config', 'status_display', 'items_found', 'items_saved', 'items_failed',
                    'duration_display', 'triggered_by', 'started_at']
    list_filter = ['status', 'scraper_config', 'triggered_by', 'started_at']
    search_fields = ['scraper_config__name', 'error_message', 'notes']
    readonly_fields = ['scraper_config', 'status', 'pages_scraped', 'items_found', 'items_saved',
                       'items_updated', 'items_skipped', 'items_failed', 'error_message', 'error_traceback',
                       'failed_urls', 'requests_made', 'bytes_downloaded', 'started_at', 'completed_at',
                       'duration_seconds', 'triggered_by']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Genel Bilgi', {
            'fields': ('scraper_config', 'status', 'triggered_by')
        }),
        ('Sonuçlar', {
            'fields': ('pages_scraped', 'items_found', 'items_saved', 'items_updated', 'items_skipped', 'items_failed')
        }),
        ('Performans', {
            'fields': ('requests_made', 'bytes_downloaded', 'duration_seconds'),
            'classes': ('collapse',)
        }),
        ('Hatalar', {
            'fields': ('error_message', 'error_traceback', 'failed_urls'),
            'classes': ('collapse',)
        }),
        ('Zamanlama', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Notlar', {
            'fields': ('notes',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'queued': 'gray',
            'started': 'blue',
            'running': 'orange',
            'success': 'green',
            'partial': 'olive',
            'failed': 'red',
            'timeout': 'purple',
            'cancelled': 'darkgray',
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
        color = colors.get(obj.status, 'black')
        icon = icons.get(obj.status, '')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{icon} {obj.get_status_display()}</span>')
    status_display.short_description = 'Durum'
    
    def duration_display(self, obj):
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.1f}s"
            elif obj.duration_seconds < 3600:
                return f"{obj.duration_seconds/60:.1f}m"
            return f"{obj.duration_seconds/3600:.1f}h"
        return "-"
    duration_display.short_description = 'Süre'


@admin.register(ScrapedContent)
class ScrapedContentAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'content_type', 'scraper_config', 'published_date', 'is_processed', 'scraped_at']
    list_filter = ['content_type', 'scraper_config', 'language', 'is_processed', 'scraped_at']
    search_fields = ['title', 'abstract', 'doi', 'external_id', 'keywords']
    readonly_fields = ['scraped_at', 'updated_at', 'external_id', 'raw_data', 'scrape_log']
    date_hierarchy = 'scraped_at'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'abstract', 'content_type', 'language')
        }),
        ('Yazarlar', {
            'fields': ('authors', 'affiliations')
        }),
        ('Yayın Bilgileri', {
            'fields': ('published_date', 'journal', 'publisher', 'doi', 'issn', 'isbn')
        }),
        ('Kategoriler', {
            'fields': ('categories', 'keywords')
        }),
        ('Dosyalar', {
            'fields': ('source_url', 'pdf_url', 'has_full_text')
        }),
        ('Özel Alanlar', {
            'fields': ('location', 'event_date', 'deadline', 'amount'),
            'classes': ('collapse',)
        }),
        ('Kaynak Bilgileri', {
            'fields': ('scraper_config', 'scrape_log', 'external_id'),
            'classes': ('collapse',)
        }),
        ('Ham Veri', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Sistem', {
            'fields': ('is_processed', 'scraped_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:70] + '...' if len(obj.title) > 70 else obj.title
    title_short.short_description = 'Başlık'
    
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
        self.message_user(request, f"{queryset.count()} içerik işlendi olarak işaretlendi.")
    mark_as_processed.short_description = "İşlendi olarak işaretle"
    
    def mark_as_unprocessed(self, request, queryset):
        queryset.update(is_processed=False)
        self.message_user(request, f"{queryset.count()} içerik işlenmedi olarak işaretlendi.")
    mark_as_unprocessed.short_description = "İşlenmedi olarak işaretle"


@admin.register(ProxyConfig)
class ProxyConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'proxy_type', 'host', 'port', 'is_active', 'is_working_display', 'fail_count', 'last_checked']
    list_filter = ['proxy_type', 'is_active', 'is_working']
    search_fields = ['name', 'host']
    readonly_fields = ['last_checked', 'fail_count', 'created_at']
    filter_horizontal = ['scrapers']
    
    fieldsets = (
        ('Proxy Bilgileri', {
            'fields': ('name', 'proxy_type', 'host', 'port')
        }),
        ('Kimlik Doğrulama', {
            'fields': ('username', 'password'),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('is_active', 'is_working', 'fail_count', 'last_checked')
        }),
        ('Scraper Atamaları', {
            'fields': ('scrapers',)
        }),
        ('Sistem', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def is_working_display(self, obj):
        if obj.is_working:
            return format_html('<span style="color: green;">✓ Çalışıyor</span>')
        return format_html('<span style="color: red;">✗ Çalışmıyor</span>')
    is_working_display.short_description = 'Durum'
    
    actions = ['check_proxies', 'reset_fail_count']
    
    def check_proxies(self, request, queryset):
        # TODO: Proxy kontrol task'ı tetikle
        self.message_user(request, f"{queryset.count()} proxy kontrol edilmek üzere kuyruğa eklendi.")
    check_proxies.short_description = "Seçili proxy'leri kontrol et"
    
    def reset_fail_count(self, request, queryset):
        queryset.update(fail_count=0, is_working=True)
        self.message_user(request, f"{queryset.count()} proxy'nin hata sayacı sıfırlandı.")
    reset_fail_count.short_description = "Hata sayacını sıfırla"
