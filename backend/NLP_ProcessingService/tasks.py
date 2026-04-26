"""
Celery Tasks for NLP Processing Service.
Handles async processing of articles through the NLP pipeline.
"""
import logging
from celery import shared_task

logger = logging.getLogger('NLP_ProcessingService')


@shared_task(name='nlp.process_article', bind=True, max_retries=3,
             default_retry_delay=60)
def process_article_task(self, external_id: str, title: str, abstract: str = "",
                         source_table: str = "article"):
    """Process a single article through the full NLP pipeline."""
    try:
        from NLP_ProcessingService.pipeline import process_single_article, save_nlp_profile
        
        logger.info(f"Processing article: {external_id[:50]}")
        result = process_single_article(external_id, title, abstract, source_table)
        save_nlp_profile(result)
        
        return {"status": "ok", "external_id": external_id}
    except Exception as exc:
        logger.error(f"NLP processing failed for {external_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(name='nlp.process_all_unprocessed')
def process_all_unprocessed_task(batch_size: int = 100):
    """
    Find all articles without NLP profiles and queue them for processing.
    Run periodically via Celery Beat.
    """
    from NLP_ProcessingService.models import ArticleNLPProfile
    
    processed_ids = set(
        ArticleNLPProfile.objects.values_list('external_id', flat=True)
    )
    
    queued = 0
    
    # Process API Articles
    try:
        from api_collecter.models import Article
        unprocessed_articles = Article.objects.exclude(
            external_id__in=processed_ids
        )[:batch_size]
        
        for article in unprocessed_articles:
            process_article_task.delay(
                article.external_id,
                article.title,
                article.abstract or "",
                "article"
            )
            queued += 1
    except Exception as e:
        logger.error(f"Failed to queue API articles: {e}")
    
    # Process Scraped Content
    try:
        from webscraping.models import ScrapedContent
        unprocessed_scraped = ScrapedContent.objects.exclude(
            external_id__in=processed_ids
        )[:batch_size]
        
        for item in unprocessed_scraped:
            process_article_task.delay(
                item.external_id,
                item.title,
                item.abstract or "",
                "scraped"
            )
            queued += 1
    except Exception as e:
        logger.error(f"Failed to queue scraped content: {e}")
    
    logger.info(f"Queued {queued} articles for NLP processing")
    return {"queued": queued}


@shared_task(name='nlp.rebuild_all_profiles')
def rebuild_all_profiles_task():
    """
    Force re-process ALL articles. Use sparingly — for model upgrades.
    """
    from NLP_ProcessingService.models import ArticleNLPProfile
    # Clear existing profiles
    ArticleNLPProfile.objects.all().delete()
    logger.info("All NLP profiles cleared. Starting rebuild...")
    return process_all_unprocessed_task(batch_size=500)
