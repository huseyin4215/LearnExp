"""
Celery Tasks for Automated Article Fetching
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from typing import Dict, Any
import time

logger = get_task_logger(__name__)


@shared_task(
    name='api_collecter.fetch_from_source',
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def fetch_from_source_task(self, config_id: int, query: str = None, max_results: int = None) -> Dict[str, Any]:
    """
    Celery task to fetch articles from a specific API source
    
    Args:
        config_id: APISourceConfig ID
        query: Optional search query override
        max_results: Optional max results override
        
    Returns:
        Result dictionary with success status and stats
    """
    from api_collecter.models import APISourceConfig
    from api_collecter.services.generic_fetcher import GenericAPIFetcher
    from api_collecter.services.rate_limiter import get_rate_limiter
    
    try:
        # Get config
        config = APISourceConfig.objects.get(id=config_id)
        
        if not config.is_active:
            logger.warning(f"Skipping inactive source: {config.name}")
            return {'success': False, 'error': 'Source is inactive'}
        
        logger.info(f"Starting fetch task for: {config.name}")
        
        # Check rate limit
        rate_limiter = get_rate_limiter(
            config.name,
            per_minute=config.rate_limit_per_minute,
            per_hour=config.rate_limit_per_hour
        )
        
        if not rate_limiter.can_make_request():
            logger.warning(f"Rate limit exceeded for {config.name}, retrying later")
            # Retry after delay
            raise self.retry(countdown=60)
        
        # Fetch articles
        fetcher = GenericAPIFetcher(config)
        result = fetcher.fetch(query, max_results)
        
        # Record request for rate limiting
        if result['success']:
            rate_limiter.record_request()
        
        logger.info(
            f"Fetch completed for {config.name}: "
            f"Found={result.get('total_found', 0)}, "
            f"Saved={result.get('saved', 0)}, "
            f"Updated={result.get('updated', 0)}"
        )
        
        return result
        
    except APISourceConfig.DoesNotExist:
        logger.error(f"API source config not found: {config_id}")
        return {'success': False, 'error': 'Config not found'}
    
    except Exception as e:
        logger.error(f"Fetch task failed for config {config_id}: {e}", exc_info=True)
        
        # Retry on failure
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for config {config_id}")
            return {'success': False, 'error': str(e), 'max_retries_exceeded': True}


@shared_task(name='api_collecter.fetch_all_active_sources')
def fetch_all_active_sources_task() -> Dict[str, Any]:
    """
    Celery task to fetch from all active API sources
    This is typically scheduled via Celery Beat
    
    Returns:
        Summary of all fetch operations
    """
    from api_collecter.models import APISourceConfig
    
    logger.info("Starting batch fetch for all active sources")
    
    # Get all active sources that are due for fetching
    active_sources = APISourceConfig.objects.filter(
        is_active=True
    )
    
    results = []
    total_success = 0
    total_failed = 0
    total_articles = 0
    
    for config in active_sources:
        # Check if it's time to fetch
        if not config.should_fetch_now():
            logger.info(f"Skipping {config.name} - not due yet (next: {config.next_fetch})")
            continue
        
        try:
            # Launch async task for each source
            result = fetch_from_source_task.delay(config.id)
            
            # Wait for result (with timeout)
            task_result = result.get(timeout=config.timeout_seconds + 30)
            
            if task_result.get('success'):
                total_success += 1
                total_articles += task_result.get('saved', 0)
            else:
                total_failed += 1
            
            results.append({
                'source': config.name,
                'success': task_result.get('success'),
                'saved': task_result.get('saved', 0),
                'error': task_result.get('error')
            })
            
            # Small delay between sources
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error fetching from {config.name}: {e}", exc_info=True)
            total_failed += 1
            results.append({
                'source': config.name,
                'success': False,
                'error': str(e)
            })
    
    summary = {
        'total_sources': len(results),
        'successful': total_success,
        'failed': total_failed,
        'total_articles_saved': total_articles,
        'results': results,
        'completed_at': timezone.now().isoformat()
    }
    
    logger.info(
        f"Batch fetch completed: {total_success} successful, "
        f"{total_failed} failed, {total_articles} articles saved"
    )
    
    return summary


@shared_task(name='api_collecter.cleanup_old_logs')
def cleanup_old_logs_task(days: int = 30) -> Dict[str, Any]:
    """
    Clean up old fetch logs
    
    Args:
        days: Delete logs older than this many days
        
    Returns:
        Cleanup summary
    """
    from api_collecter.models import APIFetchLog
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    old_logs = APIFetchLog.objects.filter(started_at__lt=cutoff_date)
    count = old_logs.count()
    old_logs.delete()
    
    logger.info(f"Cleaned up {count} old fetch logs (older than {days} days)")
    
    return {
        'deleted_count': count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task(name='api_collecter.health_check')
def health_check_task() -> Dict[str, Any]:
    """
    Health check task to monitor API sources
    Checks for sources with repeated failures
    
    Returns:
        Health status report
    """
    from api_collecter.models import APISourceConfig, APIFetchLog
    from datetime import timedelta
    
    logger.info("Running health check on API sources")
    
    issues = []
    
    # Check each active source
    active_sources = APISourceConfig.objects.filter(is_active=True)
    
    for config in active_sources:
        # Get recent logs
        recent_logs = config.fetch_logs.filter(
            started_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-started_at')[:5]
        
        if not recent_logs.exists():
            issues.append({
                'source': config.name,
                'issue': 'No recent fetch attempts',
                'severity': 'warning'
            })
            continue
        
        # Check for repeated failures
        failed_count = recent_logs.filter(status='failed').count()
        if failed_count >= 3:
            issues.append({
                'source': config.name,
                'issue': f'{failed_count} failures in last 5 attempts',
                'last_error': config.last_error,
                'severity': 'critical'
            })
        
        # Check if overdue
        if config.next_fetch and config.next_fetch < timezone.now() - timedelta(hours=2):
            issues.append({
                'source': config.name,
                'issue': f'Overdue for fetch (due: {config.next_fetch})',
                'severity': 'warning'
            })
    
    return {
        'checked_sources': active_sources.count(),
        'issues_found': len(issues),
        'issues': issues,
        'checked_at': timezone.now().isoformat()
    }


# Periodic task schedule (configure in celery.py)
"""
Example Celery Beat schedule:

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'fetch-all-sources-every-6-hours': {
        'task': 'api_collecter.fetch_all_active_sources',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'cleanup-old-logs-daily': {
        'task': 'api_collecter.cleanup_old_logs',
        'schedule': crontab(minute=0, hour=3),  # Daily at 3 AM
        'kwargs': {'days': 30}
    },
    'health-check-hourly': {
        'task': 'api_collecter.health_check',
        'schedule': crontab(minute=0),  # Every hour
    },
}
"""
