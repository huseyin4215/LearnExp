from django.contrib import admin
from .models import ArticleNLPProfile


@admin.register(ArticleNLPProfile)
class ArticleNLPProfileAdmin(admin.ModelAdmin):
    list_display = ['external_id', 'source_table', 'topic_id', 'topic_confidence', 
                     'token_count', 'language', 'processed_at']
    list_filter = ['source_table', 'language', 'topic_id']
    search_fields = ['external_id', 'keywords']
    readonly_fields = ['processed_at', 'updated_at']
    
    fieldsets = (
        ('Article Info', {
            'fields': ('external_id', 'source_table', 'embedding_model')
        }),
        ('NLP Results', {
            'fields': ('keywords', 'entities', 'topic_id', 'topic_confidence', 'topic_words')
        }),
        ('Metadata', {
            'fields': ('token_count', 'language', 'processed_at', 'updated_at')
        }),
        ('Embedding', {
            'classes': ('collapse',),
            'fields': ('embedding',),
            'description': '384-dimensional embedding vector (usually hidden)',
        }),
    )
