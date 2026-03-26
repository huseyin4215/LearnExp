"""
Web Scraping modellerinin proxy'leri
Bu sayede tüm modeller api_collecter altında görünür
"""
from webscraping.models import ScraperConfig, ScrapeLog, ScrapedContent, ProxyConfig


class ScraperKonfig(ScraperConfig):
    """ScraperConfig proxy modeli"""
    class Meta:
        proxy = True
        app_label = 'api_collecter'
        verbose_name = 'Scraper Konfigürasyonu'
        verbose_name_plural = 'Scraper Konfigürasyonları'


class ScrapeLogu(ScrapeLog):
    """ScrapeLog proxy modeli"""
    class Meta:
        proxy = True
        app_label = 'api_collecter'
        verbose_name = 'Scrape Logu'
        verbose_name_plural = 'Scrape Logları'


class ScrapeIcerik(ScrapedContent):
    """ScrapedContent proxy modeli"""
    class Meta:
        proxy = True
        app_label = 'api_collecter'
        verbose_name = 'Scrape Edilen İçerik'
        verbose_name_plural = 'Scrape Edilen İçerikler'


class ProxyKonfig(ProxyConfig):
    """ProxyConfig proxy modeli"""
    class Meta:
        proxy = True
        app_label = 'api_collecter'
        verbose_name = 'Proxy Konfigürasyonu'
        verbose_name_plural = 'Proxy Konfigürasyonları'

