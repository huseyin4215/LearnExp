"""
Celery Configuration for LearnExp
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('learnexp')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# Celery Beat Schedule - Periodic Tasks
app.conf.beat_schedule = {
    # API Collector: Fetch from all active sources every 6 hours
    'fetch-all-api-sources-every-6-hours': {
        'task': 'api_collecter.fetch_all_active_sources',
        'schedule': crontab(minute=0, hour='*/6'),
        'options': {'expires': 3600}  # Task expires after 1 hour
    },
    
    # Web Scraping: Scrape all active sources every 12 hours
    'scrape-all-sources-every-12-hours': {
        'task': 'webscraping.tasks.scrape_tasks.scrape_all_active_sources_task',
        'schedule': crontab(minute=0, hour='*/12'),
        'options': {'expires': 7200}  # Task expires after 2 hours
    },
    
    # Cleanup old API logs daily at 3 AM
    'cleanup-old-api-logs-daily': {
        'task': 'api_collecter.cleanup_old_logs',
        'schedule': crontab(minute=0, hour=3),
        'kwargs': {'days': 30}
    },
    
    # Cleanup old scrape logs daily at 3:30 AM
    'cleanup-old-scrape-logs-daily': {
        'task': 'webscraping.tasks.scrape_tasks.cleanup_old_logs_task',
        'schedule': crontab(minute=30, hour=3),
        'kwargs': {'days': 30}
    },
    
    # Health check for API sources every hour
    'health-check-api-hourly': {
        'task': 'api_collecter.health_check',
        'schedule': crontab(minute=0),
    },
    
    # Health check for scrapers every 2 hours
    'health-check-scrapers-every-2-hours': {
        'task': 'webscraping.tasks.scrape_tasks.health_check_scrapers_task',
        'schedule': crontab(minute=0, hour='*/2'),
    },
}

# Celery Configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Disable prefetching for long tasks
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
