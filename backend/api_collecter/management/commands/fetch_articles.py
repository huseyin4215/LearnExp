"""
Django Management Command for Fetching Articles
Alternative to Celery for simple deployments
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from api_collecter.models import APISourceConfig
from api_collecter.services.generic_fetcher import fetch_from_source, fetch_all_active_sources


class Command(BaseCommand):
    help = 'Fetch articles from API sources'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Specific source name to fetch from'
        )
        
        parser.add_argument(
            '--source-id',
            type=int,
            help='Specific source ID to fetch from'
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Fetch from all active sources'
        )
        
        parser.add_argument(
            '--query',
            type=str,
            help='Override default search query'
        )
        
        parser.add_argument(
            '--max-results',
            type=int,
            help='Override max results per request'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force fetch even if not due yet'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting article fetch...'))
        
        # Fetch from specific source by ID
        if options['source_id']:
            self._fetch_by_id(
                options['source_id'],
                options.get('query'),
                options.get('max_results'),
                options.get('force', False)
            )
        
        # Fetch from specific source by name
        elif options['source']:
            self._fetch_by_name(
                options['source'],
                options.get('query'),
                options.get('max_results'),
                options.get('force', False)
            )
        
        # Fetch from all active sources
        elif options['all']:
            self._fetch_all(options.get('force', False))
        
        else:
            raise CommandError('Please specify --source, --source-id, or --all')
    
    def _fetch_by_id(self, source_id, query=None, max_results=None, force=False):
        """Fetch from specific source by ID"""
        try:
            config = APISourceConfig.objects.get(id=source_id)
            self._fetch_source(config, query, max_results, force)
        except APISourceConfig.DoesNotExist:
            raise CommandError(f'Source with ID {source_id} not found')
    
    def _fetch_by_name(self, source_name, query=None, max_results=None, force=False):
        """Fetch from specific source by name"""
        try:
            config = APISourceConfig.objects.get(name=source_name)
            self._fetch_source(config, query, max_results, force)
        except APISourceConfig.DoesNotExist:
            raise CommandError(f'Source "{source_name}" not found')
    
    def _fetch_source(self, config, query=None, max_results=None, force=False):
        """Fetch from a single source"""
        if not config.is_active:
            self.stdout.write(self.style.WARNING(f'Source "{config.name}" is inactive'))
            return
        
        if not force and not config.should_fetch_now():
            self.stdout.write(
                self.style.WARNING(
                    f'Source "{config.name}" is not due for fetch yet '
                    f'(next: {config.next_fetch}). Use --force to override.'
                )
            )
            return
        
        self.stdout.write(f'Fetching from: {config.name}')
        
        result = fetch_from_source(config.id, query, max_results)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Success: Found {result["total_found"]}, '
                    f'Saved {result["saved"]}, '
                    f'Updated {result["updated"]}, '
                    f'Skipped {result["skipped"]}'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed: {result.get("error")}')
            )
    
    def _fetch_all(self, force=False):
        """Fetch from all active sources"""
        active_sources = APISourceConfig.objects.filter(is_active=True)
        
        if not active_sources.exists():
            self.stdout.write(self.style.WARNING('No active sources found'))
            return
        
        self.stdout.write(f'Found {active_sources.count()} active sources')
        
        total_success = 0
        total_failed = 0
        total_articles = 0
        
        for config in active_sources:
            if not force and not config.should_fetch_now():
                self.stdout.write(
                    self.style.WARNING(
                        f'⏭ Skipping "{config.name}" - not due yet (next: {config.next_fetch})'
                    )
                )
                continue
            
            self.stdout.write(f'\n📡 Fetching from: {config.name}')
            
            result = fetch_from_source(config.id)
            
            if result['success']:
                total_success += 1
                total_articles += result['saved']
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Found {result["total_found"]}, '
                        f'Saved {result["saved"]}, '
                        f'Updated {result["updated"]}'
                    )
                )
            else:
                total_failed += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed: {result.get("error")}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  Total sources: {active_sources.count()}')
        self.stdout.write(f'  Successful: {total_success}')
        self.stdout.write(f'  Failed: {total_failed}')
        self.stdout.write(f'  Total articles saved: {total_articles}')
        self.stdout.write('='*60)


"""
Usage Examples:

# Fetch from all active sources
python manage.py fetch_articles --all

# Fetch from specific source by name
python manage.py fetch_articles --source "arXiv Machine Learning"

# Fetch from specific source by ID
python manage.py fetch_articles --source-id 1

# Override search query
python manage.py fetch_articles --source "OpenAlex" --query "quantum computing"

# Force fetch even if not due
python manage.py fetch_articles --all --force

# Limit results
python manage.py fetch_articles --source "CrossRef" --max-results 50

# Can be scheduled with cron:
# 0 */6 * * * cd /path/to/project && python manage.py fetch_articles --all
"""
