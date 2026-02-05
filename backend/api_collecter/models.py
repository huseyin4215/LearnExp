from django.db import models
from django.utils import timezone


class APISourceConfig(models.Model):
    """API kaynakları için konfigürasyon - Makale çekme ayarları"""
    
    SOURCE_CHOICES = [
        ('arxiv', 'arXiv API'),
        ('openalex', 'OpenAlex API'),
        ('crossref', 'CrossRef API'),
        ('semantic_scholar', 'Semantic Scholar API'),
        ('pubmed', 'PubMed API'),
        ('ieee', 'IEEE Xplore API'),
        ('springer', 'Springer Nature API'),
        ('core', 'CORE API'),
        ('doaj', 'DOAJ API'),
        ('custom', 'Custom API'),
    ]
    
    name = models.CharField(max_length=100, unique=True, help_text="API kaynağı için benzersiz isim")
    source_type = models.CharField(max_length=50, choices=SOURCE_CHOICES, help_text="API türü")
    base_url = models.URLField(help_text="API base URL")
    api_key = models.CharField(max_length=500, blank=True, help_text="API anahtarı (gerekiyorsa)")
    api_secret = models.CharField(max_length=500, blank=True, help_text="API secret (gerekiyorsa)")
    
    # Arama ve çekme ayarları
    search_query = models.TextField(blank=True, help_text="Varsayılan arama sorgusu/anahtar kelimeler")
    categories = models.TextField(blank=True, help_text="Kategoriler (virgülle ayrılmış)")
    max_results_per_request = models.IntegerField(default=100, help_text="İstek başına maksimum sonuç")
    rate_limit_per_minute = models.IntegerField(default=60, help_text="Dakikada maksimum istek sayısı")
    
    # Zamanlama
    fetch_interval_hours = models.IntegerField(default=6, help_text="Kaç saatte bir çekilecek")
    is_active = models.BooleanField(default=True, help_text="Aktif/Pasif")
    last_fetch = models.DateTimeField(null=True, blank=True, help_text="Son başarılı çekme zamanı")
    next_fetch = models.DateTimeField(null=True, blank=True, help_text="Sonraki planlanan çekme")
    
    # İstatistikler
    total_articles_fetched = models.IntegerField(default=0, help_text="Toplam çekilen makale sayısı")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Kaynak Konfigürasyonu"
        verbose_name_plural = "API Kaynak Konfigürasyonları"
        ordering = ['-created_at']
    
    def __str__(self):
        status = "✓ Aktif" if self.is_active else "✗ Pasif"
        return f"{self.name} ({self.get_source_type_display()}) - {status}"


class APIFetchLog(models.Model):
    """API'den makale çekme logları"""
    
    STATUS_CHOICES = [
        ('started', 'Başladı'),
        ('fetching', 'Çekiliyor'),
        ('processing', 'İşleniyor'),
        ('success', 'Başarılı'),
        ('partial', 'Kısmi Başarı'),
        ('failed', 'Başarısız'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    api_config = models.ForeignKey(
        APISourceConfig,
        on_delete=models.CASCADE,
        related_name='fetch_logs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    
    # İstek detayları
    request_url = models.TextField(blank=True, help_text="Yapılan istek URL'i")
    request_params = models.JSONField(default=dict, blank=True, help_text="İstek parametreleri")
    
    # Sonuçlar
    articles_found = models.IntegerField(default=0, help_text="Bulunan makale sayısı")
    articles_saved = models.IntegerField(default=0, help_text="Kaydedilen makale sayısı")
    articles_updated = models.IntegerField(default=0, help_text="Güncellenen makale sayısı")
    articles_skipped = models.IntegerField(default=0, help_text="Atlanan makale sayısı (duplicate)")
    
    # Hata bilgileri
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True, help_text="Detaylı hata bilgisi")
    
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
    """API'lerden çekilen makaleler"""
    
    api_source = models.ForeignKey(
        APISourceConfig,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles'
    )
    
    # Temel bilgiler
    external_id = models.CharField(max_length=255, unique=True, help_text="Kaynak sistemdeki ID")
    title = models.TextField(help_text="Makale başlığı")
    abstract = models.TextField(blank=True, help_text="Özet")
    authors = models.JSONField(default=list, help_text="Yazarlar listesi")
    
    # Yayın bilgileri
    published_date = models.DateField(null=True, blank=True)
    journal = models.CharField(max_length=500, blank=True)
    volume = models.CharField(max_length=50, blank=True)
    issue = models.CharField(max_length=50, blank=True)
    pages = models.CharField(max_length=50, blank=True)
    doi = models.CharField(max_length=255, blank=True, unique=True, null=True)
    
    # Linkler
    url = models.URLField(blank=True)
    pdf_url = models.URLField(blank=True)
    
    # Kategoriler ve etiketler
    categories = models.JSONField(default=list, help_text="Kategoriler")
    keywords = models.JSONField(default=list, help_text="Anahtar kelimeler")
    
    # Metrikler
    citation_count = models.IntegerField(default=0)
    
    # Ham veri
    raw_data = models.JSONField(default=dict, help_text="Orijinal API yanıtı")
    
    # Sistem bilgileri
    fetched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Makale"
        verbose_name_plural = "Makaleler"
        ordering = ['-published_date', '-fetched_at']
        indexes = [
            models.Index(fields=['-published_date']),
            models.Index(fields=['doi']),
            models.Index(fields=['api_source', '-fetched_at']),
        ]
    
    def __str__(self):
        return f"{self.title[:80]}..." if len(self.title) > 80 else self.title


class CallbackConfig(models.Model):
    """Admin-editable API callback configurations"""
    
    name = models.CharField(max_length=100, unique=True, help_text="Unique name for this callback")
    endpoint_url = models.URLField(help_text="URL to send callbacks to")
    webhook_secret = models.CharField(max_length=255, help_text="Secret key for webhook validation")
    is_active = models.BooleanField(default=True, help_text="Enable/disable this callback")
    retry_count = models.IntegerField(default=3, help_text="Number of retry attempts on failure")
    timeout_seconds = models.IntegerField(default=30, help_text="Request timeout in seconds")
    
    # Event types this callback should trigger on
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
    """Log all callback attempts"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retry', 'Retrying'),
    ]
    
    config = models.ForeignKey(
        CallbackConfig,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    event_type = models.CharField(max_length=50, help_text="Type of event that triggered callback")
    request_payload = models.JSONField(help_text="Data sent to callback endpoint")
    response_status = models.IntegerField(null=True, blank=True, help_text="HTTP status code")
    response_body = models.TextField(blank=True, help_text="Response from endpoint")
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    retry_attempt = models.IntegerField(default=0, help_text="Current retry attempt number")
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
        return f"{status} {self.config.name} - {self.event_type} at {self.attempted_at}"


class WebhookReceiver(models.Model):
    """Store received webhooks from external services"""
    
    source = models.CharField(max_length=100, help_text="Source of the webhook")
    payload = models.JSONField(help_text="Received webhook payload")
    headers = models.JSONField(help_text="Request headers")
    validated = models.BooleanField(default=False, help_text="Whether webhook signature was validated")
    processed = models.BooleanField(default=False, help_text="Whether payload was processed")
    processing_error = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Webhook Receiver"
        verbose_name_plural = "Webhook Receivers"
        ordering = ['-received_at']
    
    def __str__(self):
        status = "✓ Processed" if self.processed else "⏳ Pending"
        return f"{status} - {self.source} at {self.received_at}"
