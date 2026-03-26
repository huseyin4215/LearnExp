from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import json


class APISourceConfig(models.Model):
    """
    Tamamen dinamik API konfigürasyonu
    Herhangi bir API için kullanılabilir
    """
    
    RESPONSE_FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('rss', 'RSS Feed'),
    ]
    
    HTTP_METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
    ]
    
    AUTH_TYPE_CHOICES = [
        ('none', 'No Authentication'),
        ('api_key_header', 'API Key in Header'),
        ('api_key_param', 'API Key as URL Parameter'),
        ('bearer_token', 'Bearer Token'),
        ('basic_auth', 'Basic Authentication'),
    ]
    
    # ==================== TEMEL BİLGİLER ====================
    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="API kaynağı için benzersiz isim"
    )
    description = models.TextField(
        blank=True,
        help_text="API açıklaması"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Aktif/Pasif"
    )
    
    # ==================== BAĞLANTI AYARLARI ====================
    base_url = models.URLField(
        help_text="API endpoint URL (örn: https://api.example.com/search)"
    )
    http_method = models.CharField(
        max_length=10,
        choices=HTTP_METHOD_CHOICES,
        default='GET',
        help_text="HTTP metodu"
    )
    response_format = models.CharField(
        max_length=10,
        choices=RESPONSE_FORMAT_CHOICES,
        default='json',
        help_text="API yanıt formatı"
    )
    
    # ==================== KİMLİK DOĞRULAMA ====================
    auth_type = models.CharField(
        max_length=20,
        choices=AUTH_TYPE_CHOICES,
        default='none',
        help_text="Kimlik doğrulama türü"
    )
    api_key = models.CharField(
        max_length=500, 
        blank=True,
        help_text="API anahtarı"
    )
    api_key_header_name = models.CharField(
        max_length=100,
        blank=True,
        default='X-API-Key',
        help_text="API key header adı (örn: X-API-Key, Authorization)"
    )
    api_key_param_name = models.CharField(
        max_length=100,
        blank=True,
        default='api_key',
        help_text="API key parametre adı (örn: api_key, apikey)"
    )
    api_secret = models.CharField(
        max_length=500, 
        blank=True,
        help_text="API secret (gerekiyorsa)"
    )
    
    # ==================== SORGU PARAMETRELERİ (DİNAMİK) ====================
    query_params = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Dinamik sorgu parametreleri (JSON formatında)
        Örnek: {
            "q": "{search_query}",
            "limit": "{max_results}",
            "sort": "date",
            "format": "json"
        }
        Değişkenler: {search_query}, {max_results}, {categories}
        """
    )
    
    # POST için body template
    request_body_template = models.JSONField(
        default=dict,
        blank=True,
        help_text="POST isteği için body template (JSON)"
    )
    
    # Ek headers
    custom_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Özel HTTP headers (JSON formatında)
        Örnek: {
            "User-Agent": "MyApp/1.0",
            "Accept": "application/json"
        }
        """
    )
    
    # ==================== ARAMA AYARLARI ====================
    default_search_query = models.TextField(
        blank=True,
        help_text="Varsayılan arama sorgusu"
    )
    categories = models.TextField(
        blank=True,
        help_text="Kategoriler (virgülle ayrılmış)"
    )
    max_results_per_request = models.IntegerField(
        default=100,
        help_text="İstek başına maksimum sonuç"
    )
    
    # ==================== YANIT PARSE AYARLARI (DİNAMİK) ====================
    response_data_path = models.CharField(
        max_length=500,
        default='results',
        help_text="""
        Yanıttaki veri dizisinin yolu (nokta notasyonu)
        JSON örnek: 'data.items' veya 'results'
        XML örnek: 'feed.entry' veya 'rss.channel.item'
        """
    )
    
    field_mappings = models.JSONField(
        default=dict,
        help_text="""
        Alan eşleştirmeleri (JSON formatında)
        API'den gelen alanları standart alanlara eşleştir
        Örnek: {
            "title": "title",
            "abstract": "description",
            "authors": "author_list",
            "published_date": "pub_date",
            "external_id": "id",
            "url": "link",
            "doi": "doi",
            "categories": "subjects"
        }
        Nokta notasyonu desteklenir: "metadata.title"
        """
    )
    
    # Tarih formatı
    date_format = models.CharField(
        max_length=50,
        default='%Y-%m-%d',
        blank=True,
        help_text="Tarih formatı (Python strftime formatı, örn: %Y-%m-%d, %d/%m/%Y)"
    )
    
    # Yazar parse ayarları
    author_field_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String (virgülle ayrılmış)'),
            ('array', 'Array/List'),
            ('object_array', 'Object Array (name field içeren)'),
        ],
        default='array',
        help_text="Yazar alanının formatı"
    )
    
    author_name_field = models.CharField(
        max_length=100,
        default='name',
        blank=True,
        help_text="Object array ise, isim alanının adı"
    )
    
    # ==================== RATE LIMITING ====================
    rate_limit_per_minute = models.IntegerField(
        default=60,
        help_text="Dakikada maksimum istek sayısı"
    )
    rate_limit_per_hour = models.IntegerField(
        default=1000,
        help_text="Saatte maksimum istek sayısı"
    )
    request_delay_seconds = models.FloatField(
        default=1.0,
        help_text="İstekler arası bekleme süresi (saniye)"
    )
    
    # ==================== ZAMANLAMA ====================
    fetch_interval_hours = models.IntegerField(
        default=6,
        help_text="Kaç saatte bir otomatik çekilecek"
    )
    last_fetch = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Son başarılı çekme zamanı"
    )
    next_fetch = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Sonraki planlanan çekme"
    )
    
    # ==================== İSTATİSTİKLER ====================
    total_articles_fetched = models.IntegerField(
        default=0,
        help_text="Toplam çekilen makale sayısı"
    )
    total_requests_made = models.IntegerField(
        default=0,
        help_text="Toplam yapılan istek sayısı"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Son hata mesajı"
    )
    last_error_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Son hata zamanı"
    )
    
    # ==================== GELİŞMİŞ AYARLAR ====================
    timeout_seconds = models.IntegerField(
        default=60,
        help_text="İstek timeout süresi (saniye)"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Hata durumunda maksimum deneme sayısı"
    )
    verify_ssl = models.BooleanField(
        default=True,
        help_text="SSL sertifikası doğrulaması"
    )
    
    # Pagination desteği
    supports_pagination = models.BooleanField(
        default=False,
        help_text="API sayfalama destekliyor mu?"
    )
    pagination_param_name = models.CharField(
        max_length=50,
        default='page',
        blank=True,
        help_text="Sayfa numarası parametresi adı"
    )
    pagination_start = models.IntegerField(
        default=1,
        help_text="Sayfalama başlangıç değeri (0 veya 1)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Kaynak Konfigürasyonu"
        verbose_name_plural = "API Kaynak Konfigürasyonları"
        ordering = ['-created_at']
    
    def __str__(self):
        status = "✓ Aktif" if self.is_active else "✗ Pasif"
        return f"{self.name} - {status}"
    
    def clean(self):
        """Validate configuration"""
        # Validate JSON fields
        if self.query_params:
            try:
                if isinstance(self.query_params, str):
                    json.loads(self.query_params)
            except json.JSONDecodeError:
                raise ValidationError({'query_params': 'Geçersiz JSON formatı'})
        
        if self.field_mappings:
            try:
                if isinstance(self.field_mappings, str):
                    json.loads(self.field_mappings)
            except json.JSONDecodeError:
                raise ValidationError({'field_mappings': 'Geçersiz JSON formatı'})
    
    def get_next_fetch_time(self):
        """Calculate next fetch time"""
        if self.last_fetch:
            from datetime import timedelta
            return self.last_fetch + timedelta(hours=self.fetch_interval_hours)
        return timezone.now()
    
    def should_fetch_now(self):
        """Check if it's time to fetch"""
        if not self.is_active:
            return False
        if not self.last_fetch:
            return True
        return timezone.now() >= self.get_next_fetch_time()


class APIFetchLog(models.Model):
    """API'den makale çekme logları"""
    
    STATUS_CHOICES = [
        ('queued', 'Kuyrukta'),
        ('started', 'Başladı'),
        ('fetching', 'Çekiliyor'),
        ('parsing', 'Parse Ediliyor'),
        ('saving', 'Kaydediliyor'),
        ('success', 'Başarılı'),
        ('partial', 'Kısmi Başarı'),
        ('failed', 'Başarısız'),
        ('timeout', 'Zaman Aşımı'),
        ('rate_limited', 'Rate Limit'),
    ]
    
    api_config = models.ForeignKey(
        APISourceConfig,
        on_delete=models.CASCADE,
        related_name='fetch_logs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # İstek detayları
    request_url = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, default='GET')
    request_params = models.JSONField(default=dict, blank=True)
    request_headers = models.JSONField(default=dict, blank=True)
    request_body = models.JSONField(default=dict, blank=True)
    
    # Yanıt detayları
    response_status_code = models.IntegerField(null=True, blank=True)
    response_size_bytes = models.IntegerField(null=True, blank=True)
    
    # Sonuçlar
    articles_found = models.IntegerField(default=0)
    articles_saved = models.IntegerField(default=0)
    articles_updated = models.IntegerField(default=0)
    articles_skipped = models.IntegerField(default=0)
    
    # Hata bilgileri
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Zamanlama
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    class Meta:
        verbose_name = "API Çekme Logu"
        verbose_name_plural = "API Çekme Logları"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['api_config', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.api_config.name} - {self.get_status_display()} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"


class Article(models.Model):
    """Normalized article storage"""
    
    api_source = models.ForeignKey(
        APISourceConfig,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles'
    )
    
    # Temel bilgiler
    external_id = models.CharField(max_length=500, unique=True, db_index=True)
    title = models.TextField()
    abstract = models.TextField(blank=True)
    authors = models.JSONField(default=list)
    
    # Yayın bilgileri
    published_date = models.DateField(null=True, blank=True, db_index=True)
    journal = models.CharField(max_length=500, blank=True)
    volume = models.CharField(max_length=50, blank=True)
    issue = models.CharField(max_length=50, blank=True)
    pages = models.CharField(max_length=50, blank=True)
    doi = models.CharField(max_length=255, blank=True, unique=True, null=True, db_index=True)
    
    # Linkler
    url = models.URLField(blank=True, max_length=1000)
    pdf_url = models.URLField(blank=True, max_length=1000)
    image_url = models.URLField(blank=True, max_length=1000, help_text="Resim URL")
    
    # Kategoriler ve etiketler
    categories = models.JSONField(default=list)
    keywords = models.JSONField(default=list)
    
    # Metrikler
    citation_count = models.IntegerField(default=0)
    
    # Ham veri (orijinal API yanıtı)
    raw_data = models.JSONField(default=dict)
    
    # Sistem bilgileri
    fetched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Makale"
        verbose_name_plural = "Makaleler"
        ordering = ['-published_date', '-fetched_at']
        indexes = [
            models.Index(fields=['-published_date']),
            models.Index(fields=['api_source', '-fetched_at']),
        ]
    
    def __str__(self):
        return f"{self.title[:80]}..." if len(self.title) > 80 else self.title


# Callback ve Webhook modelleri aynı kalabilir (ihtiyaca göre)
class CallbackConfig(models.Model):
    """API callback configurations"""
    
    name = models.CharField(max_length=100, unique=True)
    endpoint_url = models.URLField()
    webhook_secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    retry_count = models.IntegerField(default=3)
    timeout_seconds = models.IntegerField(default=30)
    
    trigger_on_new_content = models.BooleanField(default=True)
    trigger_on_scrape_complete = models.BooleanField(default=False)
    trigger_on_errors = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Callback Configuration"
        verbose_name_plural = "Callback Configurations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class CallbackLog(models.Model):
    """Callback attempt logs"""
    
    config = models.ForeignKey(CallbackConfig, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=50)
    request_payload = models.JSONField()
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    retry_attempt = models.IntegerField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Callback Log"
        verbose_name_plural = "Callback Logs"
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['success', '-attempted_at']),
            models.Index(fields=['config', '-attempted_at']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.config.name} - {self.event_type}"


class WebhookReceiver(models.Model):
    """Incoming webhook storage"""
    
    source = models.CharField(max_length=100)
    payload = models.JSONField()
    headers = models.JSONField()
    validated = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Webhook Receiver"
        verbose_name_plural = "Webhook Receivers"
        ordering = ['-received_at']
    
    def __str__(self):
        status = "✓ Processed" if self.processed else "⏳ Pending"
        return f"{status} - {self.source}"
