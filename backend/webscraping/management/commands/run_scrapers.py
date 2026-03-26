"""
Django Management Command for Running Scrapers
Alternative to Celery for cron-based scheduling
"""
from django.core.management.base import BaseCommand, CommandError
from webscraping.services.scraper_orchestrator import ScraperOrchestrator
from webscraping.models import ScraperConfig
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run web scrapers'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--scraper',
            type=str,
            help='Scraper name or ID to run (if not specified, runs all active)'
        )
        
        parser.add_argument(
            '--query',
            type=str,
            help='Search query'
        )
        
        parser.add_argument(
            '--max-results',
            type=int,
            help='Maximum results to scrape'
        )
        
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available scrapers'
        )
        
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode (max 5 results)'
        )
    
    def handle(self, *args, **options):
        # List scrapers
        if options['list']:
            self.list_scrapers()
            return
        
        # Run specific scraper
        if options['scraper']:
            self.run_single_scraper(
                options['scraper'],
                options.get('query'),
                options.get('max_results'),
                options.get('test', False)
            )
        else:
            # Run all active scrapers
            self.run_all_scrapers()
    
    def list_scrapers(self):
        """List all scrapers"""
        scrapers = ScraperConfig.objects.all()
        
        self.stdout.write(self.style.SUCCESS('\nAvailable Scrapers:'))
        self.stdout.write('-' * 80)
        
        for scraper in scrapers:
            status = '✓ Active' if scraper.is_active else '✗ Inactive'
            self.stdout.write(
                f"ID: {scraper.id:3d} | {status:12s} | {scraper.name:30s} | "
                f"Type: {scraper.get_source_type_display()}"
            )
        
        self.stdout.write('-' * 80)
        self.stdout.write(f"Total: {scrapers.count()} scrapers\n")
    
    def run_single_scraper(self, scraper_identifier: str, query: str = None, 
                          max_results: int = None, test_mode: bool = False):
        """Run single scraper by name or ID"""
        try:
            # Try to get by ID first
            if scraper_identifier.isdigit():
                config = ScraperConfig.objects.get(id=int(scraper_identifier))
            else:
                # Get by name
                config = ScraperConfig.objects.get(name=scraper_identifier)
            
            self.stdout.write(
                self.style.SUCCESS(f'\nRunning scraper: {config.name}')
            )
            
            if test_mode:
                max_results = 5
                self.stdout.write(self.style.WARNING('Test mode: limited to 5 results'))
            
            # Run scraper
            orchestrator = ScraperOrchestrator(config)
            result = orchestrator.scrape(
                query=query,
                max_results=max_results,
                triggered_by='manual'
            )
            
            # Display results
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✓ Success!\n"
                        f"  Saved: {result['saved']}\n"
                        f"  Updated: {result['updated']}\n"
                        f"  Skipped: {result['skipped']}\n"
                        f"  Duration: {result['duration']:.2f}s\n"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n✗ Failed: {result.get('error')}\n"
                    )
                )
                
        except ScraperConfig.DoesNotExist:
            raise CommandError(f'Scraper "{scraper_identifier}" not found')
        except Exception as e:
            raise CommandError(f'Error: {str(e)}')
    
    def run_all_scrapers(self):
        """Run all active scrapers"""
        self.stdout.write(
            self.style.SUCCESS('\nRunning all active scrapers...\n')
        )
        
        results = ScraperOrchestrator.scrape_all_active(triggered_by='manual')
        
        # Display summary
        success_count = sum(1 for r in results if r['result'].get('success'))
        total_count = len(results)
        
        self.stdout.write('-' * 80)
        
        for result_item in results:
            scraper_name = result_item['scraper']
            result = result_item['result']
            
            if result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {scraper_name:30s} | "
                        f"Saved: {result['saved']:3d} | "
                        f"Updated: {result['updated']:3d}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ {scraper_name:30s} | "
                        f"Error: {result.get('error', 'Unknown')[:40]}"
                    )
                )
        
        self.stdout.write('-' * 80)
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {success_count}/{total_count} successful\n"
            )
        )
