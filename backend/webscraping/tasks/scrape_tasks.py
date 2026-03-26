"""
Celery Tasks for Web Scraping
Asynchronous scraping operations
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scrape_from_source_task(self, config_id: int, query: str = None, 
                            max_results: int = None, triggered_by: str = 'scheduled'):
    """
    Scrape from specific source (async)
    
    Args:
        config_id: ScraperConfig ID
        query: Search query
        max_results: Max results
        triggered_by: Trigger source
    """
    from ..services.scraper_orchestrator import ScraperOrchestrator
    from ..models import ScraperConfig
    
    try:
        logger.info(f"Starting scrape task for config_id={config_id}")
        
        config = ScraperConfig.objects.get(id=config_id)
        
        orchestrator = ScraperOrchestrator(config)
        result = orchestrator.scrape(query, max_results, triggered_by)
        
        if result['success']:
            logger.info(
                f"Scrape task completed for {config.name}: "
                f"{result['saved']} saved, {result['updated']} updated"
            )
        else:
            logger.error(f"Scrape task failed for {config.name}: {result.get('error')}")
        
        return result
        
    except ScraperConfig.DoesNotExist:
        logger.error(f"ScraperConfig {config_id} not found")
        return {'success': False, 'error': 'Config not found'}
    
    except Exception as e:
        logger.error(f"Scrape task error: {e}", exc_info=True)
        
        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {'success': False, 'error': str(e)}


@shared_task
def scrape_all_active_sources_task(triggered_by: str = 'scheduled'):
    """
    Scrape all active sources (scheduled task)
    """
    from ..services.scraper_orchestrator import ScraperOrchestrator
    
    logger.info("Starting scheduled scrape for all active sources")
    
    results = ScraperOrchestrator.scrape_all_active(triggered_by)
    
    success_count = sum(1 for r in results if r['result'].get('success'))
    total_count = len(results)
    
    logger.info(
        f"Scheduled scrape completed: {success_count}/{total_count} successful"
    )
    
    return {
        'total': total_count,
        'successful': success_count,
        'failed': total_count - success_count,
        'results': results
    }


@shared_task
def cleanup_old_logs_task(days: int = 30):
    """
    Cleanup old scrape logs
    
    Args:
        days: Delete logs older than this many days
    """
    from ..models import ScrapeLog
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted_count, _ = ScrapeLog.objects.filter(
        started_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old scrape logs (older than {days} days)")
    
    return {
        'deleted': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task
def health_check_scrapers_task():
    """
    Health check for all scrapers
    Check for stale scrapers, failed runs, etc.
    """
    from ..models import ScraperConfig
    
    issues = []
    
    # Check for scrapers that haven't run in a while
    stale_threshold = timezone.now() - timedelta(days=7)
    stale_scrapers = ScraperConfig.objects.filter(
        is_active=True,
        last_run__lt=stale_threshold
    )
    
    for scraper in stale_scrapers:
        issues.append({
            'scraper': scraper.name,
            'issue': 'stale',
            'last_run': scraper.last_run.isoformat() if scraper.last_run else None
        })
    
    # Check for scrapers with low success rate
    low_success_scrapers = ScraperConfig.objects.filter(
        is_active=True,
        success_rate__lt=50,
        total_runs__gte=5
    )
    
    for scraper in low_success_scrapers:
        issues.append({
            'scraper': scraper.name,
            'issue': 'low_success_rate',
            'success_rate': scraper.success_rate
        })
    
    # Check for scrapers with recent errors
    recent_error_threshold = timezone.now() - timedelta(hours=24)
    error_scrapers = ScraperConfig.objects.filter(
        is_active=True,
        last_error_at__gte=recent_error_threshold
    ).exclude(last_error='')
    
    for scraper in error_scrapers:
        issues.append({
            'scraper': scraper.name,
            'issue': 'recent_error',
            'error': scraper.last_error,
            'error_at': scraper.last_error_at.isoformat()
        })
    
    logger.info(f"Health check completed: {len(issues)} issues found")
    
    return {
        'total_issues': len(issues),
        'issues': issues
    }


@shared_task
def test_scraper_task(config_id: int, max_results: int = 5):
    """
    Test scraper with limited results
    
    Args:
        config_id: ScraperConfig ID
        max_results: Max results for test
    """
    from ..services.scraper_orchestrator import ScraperOrchestrator
    
    logger.info(f"Testing scraper config_id={config_id}")
    
    result = ScraperOrchestrator.scrape_by_id(
        config_id,
        max_results=max_results,
        triggered_by='test'
    )
    
    return result
