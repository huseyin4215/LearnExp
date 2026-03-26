"""
Proxy modeller - 'Kaydedilen Veriler' başlığı altında görünmesi için
"""
from api_collecter.models import Article
from webscraping.models import ScrapedContent


class KaydedilenMakale(Article):
    """Article proxy - 'Kaydedilen Veriler' altında gösterilir"""
    class Meta:
        proxy = True
        app_label = 'saved_data'
        verbose_name = 'Makale'
        verbose_name_plural = 'Makaleler'


class KaydedilenIcerik(ScrapedContent):
    """ScrapedContent proxy - 'Kaydedilen Veriler' altında gösterilir"""
    class Meta:
        proxy = True
        app_label = 'saved_data'
        verbose_name = 'Scrape Edilen İçerik'
        verbose_name_plural = 'Scrape Edilen İçerikler'
