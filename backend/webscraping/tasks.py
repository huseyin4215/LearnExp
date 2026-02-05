from celery import shared_task
from django.utils import timezone
from .models import ScraperConfig, ScrapedContent, ScrapeLog
from .scrapers.arxiv_scraper import ArxivScraper
import logging

logger = logging.getLogger(__name__)


@shared_task
def run_scraper(scraper_config_id):
    """Run a specific scraper by its ID"""
    try:
        config = ScraperConfig.objects.get(id=scraper_config_id, is_active=True)
    except ScraperConfig.DoesNotExist:
        logger.error(f"Scraper config {scraper_config_id} not found or inactive")
        return
    
    # Create log entry
    log = ScrapeLog.objects.create(
        scraper_config=config,
        status='started'
    )
    
    start_time = timezone.now()
    
    try:
        # Select appropriate scraper based on source type
        if config.source_type == 'arxiv':
            scraper = ArxivScraper(config)
        # elif config.source_type == 'openalex':
        #     scraper = OpenAlexScraper(config)
        else:
            raise ValueError(f"Unsupported source type: {config.source_type}")
        
        # Run scraping
        results = scraper.scrape()
        items_saved = scraper.save_results(results)
        
        # Update log
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        log.status = 'success'
        log.items_scraped = len(results)
        log.items_saved = items_saved
        log.completed_at = end_time
        log.duration_seconds = int(duration)
        log.save()
        
        # Update config last_run
        config.last_run = timezone.now()
        config.save()
        
        logger.info(f"Scraper {config.name} completed: {items_saved}/{len(results)} items saved")
        
    except Exception as e:
        logger.error(f"Scraper {config.name} failed: {str(e)}")
        log.status = 'failed'
        log.error_message = str(e)
        log.completed_at = timezone.now()
        log.save()


@shared_task
def run_all_active_scrapers():
    """Run all active scrapers"""
    active_configs = ScraperConfig.objects.filter(is_active=True)
    
    for config in active_configs:
        run_scraper.delay(config.id)
    
    logger.info(f"Scheduled {active_configs.count()} scrapers to run")
