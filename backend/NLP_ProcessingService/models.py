from django.db import models


class ArticleNLPProfile(models.Model):
    """
    Stores the NLP-processed representation of an article.
    Links to Article or ScrapedContent via external_id.
    """
    SOURCE_CHOICES = [
        ('article', 'API Article'),
        ('scraped', 'Scraped Content'),
    ]
    
    external_id = models.CharField(max_length=500, unique=True, db_index=True)
    source_table = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='article')
    
    # NLP Outputs
    keywords = models.JSONField(default=list, help_text="Extracted keywords with scores")
    entities = models.JSONField(default=dict, help_text="Named entities (persons, orgs, locations)")
    
    # Topic modeling
    topic_id = models.IntegerField(null=True, blank=True)
    topic_confidence = models.FloatField(null=True, blank=True)
    topic_words = models.JSONField(default=list)
    
    # Embedding vector (384-dim float list)
    embedding = models.JSONField(default=list, help_text="384-dim sentence embedding vector")
    embedding_model = models.CharField(max_length=100, default="all-MiniLM-L6-v2")
    
    # Metadata
    token_count = models.IntegerField(default=0)
    language = models.CharField(max_length=10, default="en")
    
    processed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Article NLP Profile"
        verbose_name_plural = "Article NLP Profiles"
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['topic_id']),
            models.Index(fields=['source_table', 'external_id']),
        ]
    
    def __str__(self):
        return f"NLP:{self.external_id[:50]} topic={self.topic_id}"
