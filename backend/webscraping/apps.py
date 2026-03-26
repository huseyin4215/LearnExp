from django.apps import AppConfig


class WebscrapingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webscraping'
    verbose_name = 'Web Scraping (Gizli)'  # Artık api_collecter altında yönetiliyor

