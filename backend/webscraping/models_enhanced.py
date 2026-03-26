"""
Enhanced Production-Grade Scraper Models
Fully dynamic, configuration-driven web scraping
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import json


class ScraperConfig(models.Model):
    """
    Dynamic Scraper Configuration
    Supports ANY website without code changes
    """
    
    SOURCE_TYPE_CHOICES = [
        ('news', 'News/Blog'),
        ('academic', 'Academic Repository'),
        ('conference', 'Conference'),
        ('funding', 'Funding/Grant'),
        ('thesis', 'Thesis Database'),
        ('journal', 'Journal'),
        ('preprint', 'Preprint Server'),
        ('custom', 'Custom Source'),
    ]
    
    SCRAPER_ENGINE_CHOICES = [
        ('html', 'HTML Parser (BeautifulSoup)'),
        ('selenium', 'Selenium (JavaScript Support)'),
        ('playwright', 'Playwright (Modern JS)'),
        ('rss', 'RSS/Atom Feed'),
    ]
    
    SELECTOR_TYPE_CHOICES = [
        ('css', 'CSS Selectors'),
        ('xpath', 'XPath Selectors'),
        ('mixed', 'Mixed (CSS + XPath)'),
    ]
    
    # ==================== BASIC SETTINGS ====================
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Unique scraper name"
    )
    description = models.TextField(
        blank=True,
        help_text="Scraper description"
    )
    source_type = models.CharField(
        max_length=50,
        choices=SOURCE_TYPE_CHOICES,
        default='academic',
        help_text="Type of content source"
    )
    scraper_engine = models.CharField(
        max_length=20,
        choices=SCRAPER_ENGINE_CHOICES,
        default='html',
        help_text="Scraping engine to use"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this scraper"
    )
    
    # ==================== URL & CONNECTION ====================
    base_url = models.URLField(
        max_length=1000,
        help_text="Starting URL for scraping"
    )
    
    # Login support
    requires_login = models.BooleanField(
        default=False,
        help_text="Does this site require authentication?"
    )
    login_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text="Login page URL"
    )
    login_username_field = models.CharField(
        max_length=100,
        blank=True,
        default='username',
        help_text="HTML field name for username"
    )
    login_password_field = models.CharField(
        max_length=100,
        blank=True,
        default='password',
        help_text="HTML field name for password"
    )
    login_submit_selector = models.CharField(
        max_length=200,
        blank=True,
        default='button[type="submit"]',
        help_text="Submit button selector"
    )
    username = models.CharField(
        max_length=255,
        blank=True,
        help_text="Login username"
    )
    password = models.CharField(
        max_length=255,
        blank=True,
        help_text="Login password"
    )
    
    # ==================== SEARCH & FILTERING ====================
    default_search_query = models.TextField(
        blank=True,
        help_text="Default search query"
    )
    search_url_template = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Search URL template. Use {query}, {page}, {category}"
    )
    categories = models.TextField(
        blank=True,
        help_text="Categories (comma-separated)"
    )
    date_filter_start = models.DateField(
        null=True,
        blank=True,
        help_text="Only scrape items published after this date"
    )
    date_filter_end = models.DateField(
        null=True,
        blank=True,
        help_text="Only scrape items published before this date"
    )
    
    # ==================== SCRAPING SETTINGS ====================
    max_results = models.IntegerField(
        default=100,
        help_text="Maximum items to scrape"
    )
    max_pages = models.IntegerField(
        default=10,
        help_text="Maximum pages to scrape"
    )
    delay_between_requests = models.FloatField(
        default=2.0,
        help_text="Delay between requests (seconds)"
    )
    delay_between_pages = models.FloatField(
        default=5.0,
        help_text="Delay between pages (seconds)"
    )
    timeout_seconds = models.IntegerField(
        default=30,
        help_text="Request timeout (seconds)"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Max retry attempts per request"
    )
    
    # ==================== HTTP SETTINGS ====================
    user_agent = models.TextField(
        default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        help_text="User-Agent string"
    )
    custom_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Custom HTTP headers (JSON)
        Example: {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://example.com"
        }
        """
    )
    cookies = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom cookies (JSON)"
    )
    verify_ssl = models.BooleanField(
        default=True,
        help_text="Verify SSL certificates"
    )
    
    # ==================== SELECTORS (DYNAMIC) ====================
    selector_type = models.CharField(
        max_length=10,
        choices=SELECTOR_TYPE_CHOICES,
        default='css',
        help_text="Selector syntax type"
    )
    
    selectors = models.JSONField(
        default=dict,
        help_text="""
        Field selectors (JSON format)
        Example: {
            "item_container": "article.post",
            "title": {"selector": "h2.title", "attr": "text"},
            "url": {"selector": "a.link", "attr": "href"},
            "published_date": {"selector": "time", "attr": "datetime"},
            "authors": {"selector": "span.author", "attr": "text", "multiple": true},
            "pagination_next": {"selector": "a.next", "attr": "href"}
        }
        """
    )
    
    # ==================== PAGINATION ====================
    pagination_type = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No Pagination'),
            ('next_button', 'Next Button/Link'),
            ('page_numbers', 'Page Numbers'),
            ('infinite_scroll', 'Infinite Scroll'),
            ('url_pattern', 'URL Pattern ({page} in URL)'),
            ('url_increment', 'URL Increment — Page Number in Path'),
        ],
        default='next_button',
        help_text="Pagination strategy"
    )
    pagination_url_pattern = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL pattern for pagination. Use {page} placeholder. Example: https://site.com/page/{page}"
    )
    pagination_template = models.CharField(
        max_length=1000,
        blank=True,
        help_text=(
            "[URL_INCREMENT] Full URL template with {page} placeholder. "
            "Use this when the base URL does NOT work without a page number. "
            "Example: https://www.ankara.edu.tr/kategori/haberler/{page}"
        )
    )
    pagination_start_page = models.IntegerField(
        default=1,
        help_text="Starting page number"
    )
    stop_when_empty = models.BooleanField(
        default=True,
        help_text=(
            "Stop pagination automatically when a page returns 0 items. "
            "Recommended: ON for URL_INCREMENT scrapers."
        )
    )
    
    # ==================== DATA PROCESSING ====================
    date_format = models.CharField(
        max_length=50,
        blank=True,
        help_text="Date format (Python strftime). Leave empty for auto-detection"
    )
    
    content_type_detection = models.BooleanField(
        default=True,
        help_text="Auto-detect content type from title/abstract"
    )
    
    extract_full_text = models.BooleanField(
        default=False,
        help_text="Extract full article text (slower)"
    )
    
    full_text_selector = models.CharField(
        max_length=200,
        blank=True,
        help_text="Selector for full text content"
    )
    
    # ==================== RATE LIMITING ====================
    rate_limit_per_minute = models.IntegerField(
        default=30,
        help_text="Maximum requests per minute"
    )
    rate_limit_per_hour = models.IntegerField(
        default=1000,
        help_text="Maximum requests per hour"
    )
    respect_robots_txt = models.BooleanField(
        default=True,
        help_text="Respect robots.txt rules"
    )
    
    # ==================== PROXY SETTINGS ====================
    use_proxy = models.BooleanField(
        default=False,
        help_text="Use proxy rotation"
    )
    proxy_rotation_strategy = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No Rotation'),
            ('round_robin', 'Round Robin'),
            ('random', 'Random'),
            ('least_used', 'Least Used'),
        ],
        default='round_robin'
    )
    
    # ==================== SCHEDULING ====================
    scrape_interval_hours = models.IntegerField(
        default=24,
        help_text="Scrape interval in hours"
    )
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful run"
    )
    next_run = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next scheduled run"
    )
    
    # ==================== STATISTICS ====================
    total_items_scraped = models.IntegerField(
        default=0,
        help_text="Total items scraped successfully"
    )
    total_runs = models.IntegerField(
        default=0,
        help_text="Total scrape runs"
    )
    successful_runs = models.IntegerField(
        default=0,
        help_text="Successful runs"
    )
    failed_runs = models.IntegerField(
        default=0,
        help_text="Failed runs"
    )
    success_rate = models.FloatField(
        default=0.0,
        help_text="Success rate percentage"
    )
    average_items_per_run = models.FloatField(
        default=0.0,
        help_text="Average items scraped per run"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message"
    )
    last_error_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last error timestamp"
    )
    
    # ==================== METADATA ====================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_scrapers'
    )
    
    class Meta:
        verbose_name = "Scraper Configuration"
        verbose_name_plural = "Scraper Configurations"
        ordering = ['-is_active', '-created_at']
        indexes = [
            models.Index(fields=['is_active', '-next_run']),
            models.Index(fields=['source_type', 'is_active']),
        ]
    
    def __str__(self):
        status = "✓ Active" if self.is_active else "✗ Inactive"
        return f"{self.name} ({self.get_source_type_display()}) - {status}"
    
    def clean(self):
        """Validate configuration"""
        # Validate JSON fields
        if self.selectors:
            try:
                if isinstance(self.selectors, str):
                    json.loads(self.selectors)
            except json.JSONDecodeError:
                raise ValidationError({'selectors': 'Invalid JSON format'})
        
        # Validate login fields
        if self.requires_login:
            if not self.login_url:
                raise ValidationError({'login_url': 'Login URL required when authentication is enabled'})
            if not self.username or not self.password:
                raise ValidationError('Username and password required for login')
    
    def should_run_now(self):
        """Check if scraper should run now"""
        if not self.is_active:
            return False
        if not self.last_run:
            return True
        if not self.next_run:
            return True
        return timezone.now() >= self.next_run
    
    def calculate_next_run(self):
        """Calculate next run time"""
        from datetime import timedelta
        if self.last_run:
            return self.last_run + timedelta(hours=self.scrape_interval_hours)
        return timezone.now() + timedelta(hours=self.scrape_interval_hours)
    
    def update_statistics(self, success: bool, items_count: int = 0):
        """Update scraper statistics"""
        self.total_runs += 1
        if success:
            self.successful_runs += 1
            self.total_items_scraped += items_count
        else:
            self.failed_runs += 1
        
        # Calculate success rate
        self.success_rate = (self.successful_runs / self.total_runs * 100) if self.total_runs > 0 else 0
        
        # Calculate average items per run
        self.average_items_per_run = (self.total_items_scraped / self.successful_runs) if self.successful_runs > 0 else 0
        
        self.save()


# ScrapeLog and ScrapedContent models remain similar but with enhancements
# (keeping existing models from your codebase)
