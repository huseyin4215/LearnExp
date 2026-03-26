from celery import shared_task
from django.utils import timezone
from .models import ScraperConfig, ScrapedContent, ScrapeLog
from .scrapers.arxiv_scraper import ArxivScraper
import logging

logger = logging.getLogger(__name__)


@shared_task
def run_scraper(scraper_config_id, query=None, max_results=None, triggered_by='scheduled'):
    """Run a specific scraper by its ID using the orchestrator"""
    from .services.scraper_orchestrator import ScraperOrchestrator
    return ScraperOrchestrator.scrape_by_id(
        scraper_config_id, 
        query=query, 
        max_results=max_results, 
        triggered_by=triggered_by
    )


@shared_task
def run_all_active_scrapers():
    """Run all active scrapers using the orchestrator"""
    from .services.scraper_orchestrator import ScraperOrchestrator
    results = ScraperOrchestrator.scrape_all_active(triggered_by='scheduled')
    logger.info(f"Triggered {len(results)} active scrapers via orchestrator")
    return results
