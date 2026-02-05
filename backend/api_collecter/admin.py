from django.contrib import admin
from django.utils.html import format_html
from .models import APISourceConfig, APIFetchLog, Article, CallbackConfig, CallbackLog, WebhookReceiver


@admin.register(APISourceConfig)
class APISourceConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'is_active_display', 'fetch_interval_hours', 'last_fetch', 'total_articles_fetched', 'next_fetch']
    list_filter = ['source_type', 'is_active', 'created_at']
    search_fields = ['name', 'search_query', 'categories']
    readonly_fields = ['created_at', 'updated_at', 'last_fetch', 'next_fetch', 'total_articles_fetched']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'source_type', 'is_active')
        }),
        ('API Bağlantı Ayarları', {
            'fields': ('base_url', 'api_key', 'api_secret')
        }),
        ('Arama Ayarları', {
            'fields': ('search_query', 'categories', 'max_results_per_request', 'rate_limit_per_minute')
        }),
        ('Zamanlama', {
            'fields': ('fetch_interval_hours', 'last_fetch', 'next_fetch')
        }),
        ('İstatistikler', {
            'fields': ('total_articles_fetched',),
            'classes': ('collapse',)
        }),
        ('Sistem Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Aktif</span>')
        return format_html('<span style="color: red;">✗ Pasif</span>')
    is_active_display.short_description = 'Durum'
    
    actions = ['activate_sources', 'deactivate_sources']
    
    def activate_sources(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} kaynak aktif edildi.")
    activate_sources.short_description = "Seçili kaynakları aktif et"
    
    def deactivate_sources(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} kaynak pasif edildi.")
    deactivate_sources.short_description = "Seçili kaynakları pasif et"


@admin.register(APIFetchLog)
class APIFetchLogAdmin(admin.ModelAdmin):
    list_display = ['api_config', 'status_display', 'articles_found', 'articles_saved', 'duration_display', 'started_at']
    list_filter = ['status', 'api_config', 'started_at']
    search_fields = ['api_config__name', 'error_message']
    readonly_fields = ['api_config', 'status', 'request_url', 'request_params', 'articles_found', 
                       'articles_saved', 'articles_updated', 'articles_skipped', 'error_message', 
                       'error_details', 'started_at', 'completed_at', 'duration_seconds']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Genel Bilgi', {
            'fields': ('api_config', 'status')
        }),
        ('İstek Detayları', {
            'fields': ('request_url', 'request_params'),
            'classes': ('collapse',)
        }),
        ('Sonuçlar', {
            'fields': ('articles_found', 'articles_saved', 'articles_updated', 'articles_skipped')
        }),
        ('Hata Bilgileri', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
        ('Zamanlama', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'started': 'blue',
            'fetching': 'orange',
            'processing': 'purple',
            'success': 'green',
            'partial': 'olive',
            'failed': 'red',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{obj.get_status_display()}</span>')
    status_display.short_description = 'Durum'
    
    def duration_display(self, obj):
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.1f}s"
            return f"{obj.duration_seconds/60:.1f}m"
        return "-"
    duration_display.short_description = 'Süre'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'api_source', 'published_date', 'citation_count', 'fetched_at']
    list_filter = ['api_source', 'published_date', 'fetched_at']
    search_fields = ['title', 'abstract', 'doi', 'external_id']
    readonly_fields = ['external_id', 'fetched_at', 'updated_at', 'raw_data']
    date_hierarchy = 'fetched_at'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'abstract', 'authors')
        }),
        ('Yayın Bilgileri', {
            'fields': ('published_date', 'journal', 'volume', 'issue', 'pages', 'doi')
        }),
        ('Linkler', {
            'fields': ('url', 'pdf_url')
        }),
        ('Kategoriler', {
            'fields': ('categories', 'keywords')
        }),
        ('Metrikler', {
            'fields': ('citation_count',)
        }),
        ('Kaynak Bilgileri', {
            'fields': ('api_source', 'external_id'),
            'classes': ('collapse',)
        }),
        ('Ham Veri', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Sistem', {
            'fields': ('fetched_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:80] + '...' if len(obj.title) > 80 else obj.title
    title_short.short_description = 'Başlık'


@admin.register(CallbackConfig)
class CallbackConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'endpoint_url', 'is_active', 'retry_count', 'created_at']
    list_filter = ['is_active', 'trigger_on_new_content', 'trigger_on_scrape_complete', 'trigger_on_errors']
    search_fields = ['name', 'endpoint_url']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'endpoint_url', 'is_active')
        }),
        ('Security', {
            'fields': ('webhook_secret',)
        }),
        ('Configuration', {
            'fields': ('retry_count', 'timeout_seconds')
        }),
        ('Event Triggers', {
            'fields': ('trigger_on_new_content', 'trigger_on_scrape_complete', 'trigger_on_errors')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CallbackLog)
class CallbackLogAdmin(admin.ModelAdmin):
    list_display = ['config', 'event_type', 'success', 'response_status', 'retry_attempt', 'attempted_at']
    list_filter = ['success', 'event_type', 'config', 'attempted_at']
    search_fields = ['event_type', 'error_message']
    readonly_fields = ['attempted_at', 'completed_at', 'request_payload', 'response_body']
    date_hierarchy = 'attempted_at'
    
    fieldsets = (
        ('Callback Information', {
            'fields': ('config', 'event_type', 'success')
        }),
        ('Request', {
            'fields': ('request_payload',)
        }),
        ('Response', {
            'fields': ('response_status', 'response_body')
        }),
        ('Error Details', {
            'fields': ('error_message', 'retry_attempt')
        }),
        ('Timing', {
            'fields': ('attempted_at', 'completed_at')
        }),
    )


@admin.register(WebhookReceiver)
class WebhookReceiverAdmin(admin.ModelAdmin):
    list_display = ['source', 'validated', 'processed', 'received_at', 'processed_at']
    list_filter = ['validated', 'processed', 'source', 'received_at']
    search_fields = ['source', 'processing_error']
    readonly_fields = ['received_at', 'processed_at', 'payload', 'headers']
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('Webhook Information', {
            'fields': ('source', 'validated', 'processed')
        }),
        ('Data', {
            'fields': ('payload', 'headers')
        }),
        ('Processing', {
            'fields': ('processing_error',)
        }),
        ('Timestamps', {
            'fields': ('received_at', 'processed_at')
        }),
    )
