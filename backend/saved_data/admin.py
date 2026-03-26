"""
Kaydedilen Veriler Admin Paneli
Makaleler ve Scrape Edilen İçerikler
"""
from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import KaydedilenMakale, KaydedilenIcerik


# ============================================================================
# MAKALELER
# ============================================================================

@admin.register(KaydedilenMakale)
class KaydedilenMakaleAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'api_source', 'published_date', 'citation_count', 'fetched_at']
    list_filter = ['api_source', 'published_date', 'fetched_at']
    search_fields = ['title', 'abstract', 'doi', 'external_id']
    readonly_fields = ['external_id', 'fetched_at', 'updated_at', 'raw_data']
    date_hierarchy = 'fetched_at'
    ordering = ['-fetched_at']
    
    fieldsets = (
        ('📄 Makale Bilgileri', {
            'fields': ('title', 'abstract', 'authors')
        }),
        ('📚 Yayın Bilgileri', {
            'fields': ('published_date', 'journal', 'volume', 'issue', 'pages', 'doi')
        }),
        ('🔗 Bağlantılar', {
            'fields': ('url', 'pdf_url')
        }),
        ('🏷️ Kategoriler', {
            'fields': ('categories', 'keywords')
        }),
        ('📈 Metrikler', {
            'fields': ('citation_count',)
        }),
        ('🔌 Kaynak', {
            'fields': ('api_source', 'external_id'),
            'classes': ('collapse',)
        }),
        ('📦 Ham Veri', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('📅 Sistem', {
            'fields': ('fetched_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:70] + '...' if len(obj.title) > 70 else obj.title
    title_short.short_description = 'Başlık'


# ============================================================================
# SCRAPE EDİLEN İÇERİKLER
# ============================================================================

@admin.register(KaydedilenIcerik)
class KaydedilenIcerikAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'content_type', 'scraper_config', 'published_date', 
                    'is_processed', 'scraped_at']
    list_filter = ['content_type', 'scraper_config', 'language', 'is_processed', 'scraped_at']
    search_fields = ['title', 'abstract', 'doi', 'external_id', 'keywords']
    readonly_fields = ['scraped_at', 'updated_at', 'external_id', 'raw_data', 'scrape_log']
    date_hierarchy = 'scraped_at'
    ordering = ['-scraped_at']
    
    fieldsets = (
        ('📄 İçerik Bilgileri', {
            'fields': ('title', 'abstract', 'content_type', 'language')
        }),
        ('👤 Yazar Bilgileri', {
            'fields': ('authors', 'affiliations')
        }),
        ('📚 Yayın Bilgileri', {
            'fields': ('published_date', 'journal', 'publisher', 'doi', 'issn', 'isbn')
        }),
        ('🏷️ Kategoriler', {
            'fields': ('categories', 'keywords')
        }),
        ('📁 Dosyalar', {
            'fields': ('source_url', 'pdf_url', 'has_full_text')
        }),
        ('📍 Özel Alanlar', {
            'fields': ('location', 'event_date', 'deadline', 'amount'),
            'classes': ('collapse',),
            'description': 'Konferans, fon vb. için özel alanlar'
        }),
        ('🔌 Kaynak', {
            'fields': ('scraper_config', 'scrape_log', 'external_id'),
            'classes': ('collapse',)
        }),
        ('📦 Ham Veri', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('📅 Sistem', {
            'fields': ('is_processed', 'scraped_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Başlık'
    
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    @admin.action(description="✅ İşlendi olarak işaretle")
    def mark_as_processed(self, request, queryset):
        count = queryset.update(is_processed=True)
        self.message_user(request, f"{count} içerik işlendi olarak işaretlendi.")
    
    @admin.action(description="⏳ İşlenmedi olarak işaretle")
    def mark_as_unprocessed(self, request, queryset):
        count = queryset.update(is_processed=False)
        self.message_user(request, f"{count} içerik işlenmedi olarak işaretlendi.")
