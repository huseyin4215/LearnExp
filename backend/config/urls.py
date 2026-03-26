from django.contrib import admin
from django.urls import path, include
from api.views import search_live_from_apis

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/search/live/', search_live_from_apis, name='search_live_direct'),
    path('api/', include('api.urls')),
]
