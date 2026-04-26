from django.urls import path
from . import views

urlpatterns = [
    # Personalized recommendations
    path('', views.get_recommendations, name='get_recommendations'),
    
    # Similar articles
    path('similar/', views.get_similar_articles, name='similar_articles'),
    
    # NLP processing status
    path('nlp-status/', views.nlp_status, name='nlp_status'),
    
    # Trigger NLP processing manually
    path('process/', views.trigger_nlp_processing, name='trigger_nlp'),
]
