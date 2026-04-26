from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('user/<int:user_id>/', views.get_user, name='get_user'),
    path('user/<int:user_id>/profile/', views.update_profile, name='update_profile'),
    path('profile/update/', views.update_current_user_profile, name='update_current_profile'),
    path('interests/', views.get_interests_list, name='interests_list'),
    
    # API Sources (Makale çekme kaynakları)
    path('sources/', views.get_api_sources, name='api_sources'),
    path('sources/<int:source_id>/fetch/', views.fetch_from_api_source, name='fetch_from_source'),
    path('sources/fetch-all/', views.fetch_all_api_sources, name='fetch_all_sources'),
    
    # Scrapers (Web scraping)
    path('scrapers/', views.get_scrapers, name='scrapers'),
    path('scrapers/<int:scraper_id>/run/', views.run_scraper, name='run_scraper'),
    path('scrapers/run-all/', views.run_all_scrapers, name='run_all_scrapers'),
    
    # Articles (Makaleler)
    path('articles/', views.get_articles, name='articles'),
    path('articles/<int:article_id>/', views.get_article, name='article_detail'),
    path('articles/categories/', views.get_categories_list, name='categories_list'),
    path('sources/list/', views.get_api_sources_list, name='sources_list'),
    
    # Live Search (Canlı API araması)
    path('search/live/', views.search_live_from_apis, name='search_live'),
    
    # Scraped Contents (Scrape edilen içerikler)
    path('contents/', views.get_scraped_contents, name='scraped_contents'),
    
    # Library (Kullanıcı Kütüphanesi)
    path('library/', views.library_list, name='library_list'),
    path('library/save/', views.library_save, name='library_save'),
    path('library/remove/', views.library_remove, name='library_remove'),
    path('library/check/', views.library_check, name='library_check'),
    
    # Activity (Kullanıcı Aktiviteleri)
    path('activity/record/', views.record_activity, name='record_activity'),
    path('activity/recent/', views.get_recent_activities, name='recent_activities'),
]
