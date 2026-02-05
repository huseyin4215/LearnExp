from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ScraperConfig(models.Model):
    """Web scraping konfigürasyonları"""
    
    SOURCE_CHOICES = [
        ('arxiv', 'arXiv'),
        ('openalex', 'OpenAlex'),
        ('tubitak', 'TÜBİTAK'),
        ('yok_tez', 'YÖK Tez Merkezi'),
        ('dergipark', 'DergiPark'),
        ('google_scholar', 'Google Scholar'),
        ('researchgate', 'ResearchGate'),
        ('academia', 'Academia.edu'),
        ('custom', 'Özel Kaynak'),
    ]
    
    SCRAPER_TYPE_CHOICES = [
        ('api', 'API Tabanlı'),
        ('html', 'HTML Parsing'),
        ('selenium', 'Selenium (JavaScript)'),
        ('rss', 'RSS Feed'),
    ]
    
    name = models.CharField(max_length=100, unique=True, help_text="Scraper için benzersiz isim")
    source_type = models.CharField(max_length=50, choices=SOURCE_CHOICES, help_text="Kaynak türü")
    scraper_type = models.CharField(max_length=20, choices=SCRAPER_TYPE_CHOICES, default='html', help_text="Scraping yöntemi")
    
    # URL ve bağlantı ayarları
    base_url = models.URLField(help_text="Temel URL")
    login_url = models.URLField(blank=True, help_text="Giriş URL'i (gerekiyorsa)")
    username = models.CharField(max_length=255, blank=True, help_text="Giriş kullanıcı adı")
    password = models.CharField(max_length=255, blank=True, help_text="Giriş şifresi")
    
    # Arama ve filtreleme
    search_query = models.TextField(help_text="Arama sorgusu/anahtar kelimeler")
    categories = models.TextField(blank=True, help_text="Kategoriler (virgülle ayrılmış)")
    date_filter_start = models.DateField(null=True, blank=True, help_text="Başlangıç tarihi filtresi")
    date_filter_end = models.DateField(null=True, blank=True, help_text="Bitiş tarihi filtresi")
    
    # Scraping ayarları
    max_results = models.IntegerField(default=100, help_text="Maksimum sonuç sayısı")
    max_pages = models.IntegerField(default=10, help_text="Maksimum sayfa sayısı")
    delay_between_requests = models.FloatField(default=2.0, help_text="İstekler arası bekleme (saniye)")
    timeout_seconds = models.IntegerField(default=30, help_text="İstek timeout süresi")
    
    # User-Agent ve headers
    user_agent = models.TextField(
        default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        help_text="User-Agent header"
    )
    custom_headers = models.JSONField(default=dict, blank=True, help_text="Özel HTTP headers")
    
    # CSS/XPath seçiciler (HTML parsing için)
    selectors = models.JSONField(default=dict, blank=True, help_text="CSS/XPath seçicileri")
    
    # Zamanlama
    scrape_interval_hours = models.IntegerField(default=24, help_text="Kaç saatte bir çalışacak")
    is_active = models.BooleanField(default=True, help_text="Aktif/Pasif")
    last_run = models.DateTimeField(null=True, blank=True, help_text="Son çalışma zamanı")
    next_run = models.DateTimeField(null=True, blank=True, help_text="Sonraki planlanan çalışma")
    
    # İstatistikler
    total_items_scraped = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0, help_text="Başarı oranı (%)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Scraper Konfigürasyonu"
        verbose_name_plural = "Scraper Konfigürasyonları"
        ordering = ['-created_at']
    
    def __str__(self):
        status = "✓ Aktif" if self.is_active else "✗ Pasif"
        return f"{self.name} ({self.get_source_type_display()}) - {status}"


class ScrapeLog(models.Model):
    """Scraping işlem logları"""
    
    STATUS_CHOICES = [
        ('queued', 'Sırada'),
        ('started', 'Başladı'),
        ('running', 'Çalışıyor'),
        ('success', 'Başarılı'),
        ('partial', 'Kısmi Başarı'),
        ('failed', 'Başarısız'),
        ('timeout', 'Zaman Aşımı'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    scraper_config = models.ForeignKey(
        ScraperConfig,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # İşlem detayları
    pages_scraped = models.IntegerField(default=0, help_text="Taranan sayfa sayısı")
    items_found = models.IntegerField(default=0, help_text="Bulunan öğe sayısı")
    items_saved = models.IntegerField(default=0, help_text="Kaydedilen öğe sayısı")
    items_updated = models.IntegerField(default=0, help_text="Güncellenen öğe sayısı")
    items_skipped = models.IntegerField(default=0, help_text="Atlanan öğe sayısı")
    items_failed = models.IntegerField(default=0, help_text="Başarısız öğe sayısı")
    
    # Hata bilgileri
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True, help_text="Tam hata izi")
    failed_urls = models.JSONField(default=list, blank=True, help_text="Başarısız URL'ler")
    
    # Performans metrikleri
    requests_made = models.IntegerField(default=0, help_text="Yapılan istek sayısı")
    bytes_downloaded = models.BigIntegerField(default=0, help_text="İndirilen veri (byte)")
    
    # Zamanlama
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    # Ek bilgiler
    triggered_by = models.CharField(max_length=50, default='scheduled', help_text="manual/scheduled/api")
    notes = models.TextField(blank=True, help_text="Ek notlar")
    
    class Meta:
        verbose_name = "Scrape Logu"
        verbose_name_plural = "Scrape Logları"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['scraper_config', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.scraper_config.name} - {self.get_status_display()} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"


class ScrapedContent(models.Model):
    """Scrape edilen içerikler"""
    
    CONTENT_TYPE_CHOICES = [
        ('article', 'Makale'),
        ('thesis', 'Tez'),
        ('conference', 'Konferans'),
        ('book', 'Kitap'),
        ('book_chapter', 'Kitap Bölümü'),
        ('report', 'Rapor'),
        ('funding', 'Fon/Hibe'),
        ('event', 'Etkinlik'),
        ('other', 'Diğer'),
    ]
    
    scraper_config = models.ForeignKey(
        ScraperConfig, 
        on_delete=models.CASCADE,
        related_name='scraped_contents'
    )
    scrape_log = models.ForeignKey(
        ScrapeLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contents'
    )
    
    # Kimlik bilgileri
    external_id = models.CharField(max_length=255, help_text="Kaynak sistemdeki ID")
    source_url = models.URLField(help_text="Kaynak URL")
    
    # İçerik bilgileri
    title = models.TextField(help_text="Başlık")
    abstract = models.TextField(blank=True, help_text="Özet/Açıklama")
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES, default='article')
    
    # Yazar bilgileri
    authors = models.JSONField(default=list, help_text="Yazarlar listesi")
    affiliations = models.JSONField(default=list, blank=True, help_text="Kurumlar")
    
    # Yayın bilgileri
    published_date = models.DateField(null=True, blank=True)
    journal = models.CharField(max_length=500, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    doi = models.CharField(max_length=255, blank=True)
    issn = models.CharField(max_length=50, blank=True)
    isbn = models.CharField(max_length=50, blank=True)
    
    # Kategoriler ve etiketler
    categories = models.JSONField(default=list, help_text="Kategoriler")
    keywords = models.JSONField(default=list, help_text="Anahtar kelimeler")
    language = models.CharField(max_length=10, default='en', help_text="Dil kodu")
    
    # Dosyalar
    pdf_url = models.URLField(blank=True)
    has_full_text = models.BooleanField(default=False)
    
    # Özel alanlar (konferans, fon vb. için)
    location = models.CharField(max_length=255, blank=True, help_text="Konum (konferans için)")
    event_date = models.DateField(null=True, blank=True, help_text="Etkinlik tarihi")
    deadline = models.DateField(null=True, blank=True, help_text="Son başvuru tarihi")
    amount = models.CharField(max_length=100, blank=True, help_text="Fon miktarı")
    
    # Ham veri
    raw_data = models.JSONField(default=dict, help_text="Orijinal scrape edilen veri")
    
    # Sistem bilgileri
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_processed = models.BooleanField(default=False, help_text="NLP ile işlendi mi?")
    
    class Meta:
        verbose_name = "Scrape Edilen İçerik"
        verbose_name_plural = "Scrape Edilen İçerikler"
        ordering = ['-scraped_at']
        unique_together = ['scraper_config', 'external_id']
        indexes = [
            models.Index(fields=['content_type', '-scraped_at']),
            models.Index(fields=['external_id']),
            models.Index(fields=['doi']),
            models.Index(fields=['-published_date']),
        ]
    
    def __str__(self):
        return f"{self.title[:60]}..." if len(self.title) > 60 else self.title


class ProxyConfig(models.Model):
    """Proxy konfigürasyonları"""
    
    PROXY_TYPE_CHOICES = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
        ('socks4', 'SOCKS4'),
        ('socks5', 'SOCKS5'),
    ]
    
    name = models.CharField(max_length=100, help_text="Proxy adı")
    proxy_type = models.CharField(max_length=10, choices=PROXY_TYPE_CHOICES, default='http')
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_working = models.BooleanField(default=True, help_text="Son kontrolde çalışıyor muydu?")
    last_checked = models.DateTimeField(null=True, blank=True)
    fail_count = models.IntegerField(default=0)
    
    # Hangi scraper'lar için kullanılacak
    scrapers = models.ManyToManyField(ScraperConfig, blank=True, related_name='proxies')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Proxy Konfigürasyonu"
        verbose_name_plural = "Proxy Konfigürasyonları"
    
    def __str__(self):
        status = "✓" if self.is_working else "✗"
        return f"{status} {self.name} ({self.host}:{self.port})"
    
    def get_proxy_url(self):
        if self.username and self.password:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type}://{self.host}:{self.port}"
