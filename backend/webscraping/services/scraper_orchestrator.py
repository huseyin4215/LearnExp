"""
Scraper Orchestrator
Main controller for scraping operations
Coordinates engines, processors, and services
"""
from typing import Dict, Any, List
from django.utils import timezone
from datetime import timedelta
import logging
import traceback

from ..engines.factory import ScraperEngineFactory
from ..engines.base_engine import ScrapedItem
from .rate_limiter import RateLimiter
from .retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """
    Main orchestrator for scraping operations
    
    Responsibilities:
    1. Load configuration
    2. Select and initialize engine
    3. Apply rate limiting
    4. Execute scraping
    5. Normalize and save data
    6. Update statistics
    7. Handle errors
    """
    
    def __init__(self, config):
        """
        Args:
            config: ScraperConfig model instance
        """
        self.config = config
        self.rate_limiter = RateLimiter(config)
        self.retry_handler = RetryHandler(config)
        self.scrape_log = None
    
    def scrape(self, query: str = None, max_results: int = None, 
               triggered_by: str = 'manual', test_mode: bool = False,
               url_override: str = None, use_step1_selectors: bool = False,
               use_step2_selectors: bool = False) -> Dict[str, Any]:
        """
        Execute scraping operation
        
        Args:
            query: Search query (overrides config default)
            max_results: Max results (overrides config)
            triggered_by: 'manual', 'scheduled', 'api'
            url_override: Optional URL to visit instead of config.base_url
            use_step1_selectors: If True, use step1_selectors instead of default
            use_step2_selectors: If True, use step2_selectors instead of default
            
        Returns:
            {
                'success': bool,
                'items': List[ScrapedItem],
                'saved': int,
                'updated': int,
                'skipped': int,
                'error': str (if failed)
            }
        """
        from ..models import ScrapeLog
        
        # Create log (only if not in test mode)
        if not test_mode:
            self.scrape_log = ScrapeLog.objects.create(
                scraper_config=self.config,
                status='started',
                triggered_by=triggered_by
            )
        
        start_time = timezone.now()
        
        try:
            # Validate config is active
            if not self.config.is_active:
                raise Exception("Scraper is not active")
            
            # Update log status
            if self.scrape_log:
                self.scrape_log.status = 'running'
                self.scrape_log.save()
            
            # --- MULTI-STEP DETECTION ---
            # If multi-step is enabled and we are not already in a step-specific call
            if self.config.enable_multi_step and triggered_by != 'crawler' and not use_step1_selectors and not use_step2_selectors:
                logger.info(f"Multi-step crawling enabled for {self.config.name}. Switching to crawler mode.")
                return self.crawl(query=query, test_mode=test_mode)

            # --- ENGINE SETUP ---
            self.engine = ScraperEngineFactory.create_engine(self.config)
            
            # Switch selectors if requested (Step 1 or Step 2 overrides)
            if use_step1_selectors and self.config.step1_selectors:
                self.config.selectors = self.config.step1_selectors
                logger.debug("Using Stage 1 (Discovery) selectors")
            elif use_step2_selectors and self.config.step2_selectors:
                self.config.selectors = self.config.step2_selectors
                # Also ensure we don't paginate on Step 2 pages unless configured otherwise
                # but for now we follow the user's "Stage 2 extracting final data" logic.
                logger.debug("Using Stage 2 (Extraction) selectors")

            self.engine.setup()

            # --- NAVIGATION & EXTRACTION ---
            url = url_override or self.config.base_url
            if query:
                self.engine.query = query

            content = self.engine.navigate_to_page(url)
            
            # Execute scraping with retry logic
            items = self.retry_handler.execute_with_retry(
                lambda: self.engine.scrape(query, max_results)
            )
            
            # Update log with engine statistics
            stats = self.engine.get_statistics()
            if self.scrape_log:
                self.scrape_log.pages_scraped = stats['pages_scraped']
                self.scrape_log.requests_made = stats['requests_made']
                self.scrape_log.bytes_downloaded = stats['bytes_downloaded']
                self.scrape_log.failed_urls = stats['failed_urls']
                self.scrape_log.items_found = len(items)
                self.scrape_log.save()
            
            # Save items to database (only if not in test mode)
            if not test_mode:
                saved, updated, skipped = self._save_items(items)
                
                # Mark as success
                duration = (timezone.now() - start_time).total_seconds()
                self.scrape_log.status = 'success' if saved > 0 else 'partial'
                self.scrape_log.items_saved = saved
                self.scrape_log.items_updated = updated
                self.scrape_log.items_skipped = skipped
                self.scrape_log.completed_at = timezone.now()
                self.scrape_log.duration_seconds = duration
                self.scrape_log.save()
                
                # Update config statistics
                self._update_config_statistics(success=True, items_count=saved)
            else:
                saved, updated, skipped = 0, 0, 0
                duration = (timezone.now() - start_time).total_seconds()
            
            logger.info(
                f"Scraping completed for {self.config.name}: "
                f"{saved} saved, {updated} updated, {skipped} skipped"
            )
            
            return {
                'success': True,
                'items': [i.to_dict() if hasattr(i, 'to_dict') else i for i in items[:10]],  # Return first 10 for preview
                'total_found': len(items),
                'saved': saved,
                'updated': updated,
                'skipped': skipped,
                'duration': duration,
                'log_id': self.scrape_log.id if self.scrape_log else None,
                'test_mode': test_mode
            }
            
        except Exception as e:
            # Handle failure
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            logger.error(f"Scraping failed for {self.config.name}: {error_msg}")
            logger.debug(error_trace)
            
            duration = (timezone.now() - start_time).total_seconds()
            if self.scrape_log:
                self.scrape_log.status = 'failed'
                self.scrape_log.error_message = error_msg
                self.scrape_log.error_traceback = error_trace
                self.scrape_log.completed_at = timezone.now()
                self.scrape_log.duration_seconds = duration
                self.scrape_log.save()
            
            # Update config with error
            if not test_mode:
                self._update_config_statistics(success=False, error=error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'items': [],
                'saved': 0,
                'updated': 0,
                'skipped': 0,
                'duration': duration,
                'log_id': self.scrape_log.id if self.scrape_log else None,
                'test_mode': test_mode
            }
    
    def _save_items(self, items: List[ScrapedItem]) -> tuple:
        """
        Save scraped items to database
        
        Returns:
            (saved, updated, skipped) counts
        """
        from ..models import ScrapedContent
        
        saved = 0
        updated = 0
        skipped = 0
        
        for item in items:
            try:
                # Validate item
                if not item.validate():
                    skipped += 1
                    continue
                
                # Check if exists
                existing = ScrapedContent.objects.filter(
                    scraper_config=self.config,
                    external_id=item.external_id
                ).first()
                
                if existing:
                    # Update existing
                    item_dict = item.to_dict()
                    if 'url' in item_dict and 'source_url' not in item_dict:
                        item_dict['source_url'] = item_dict.pop('url')
                        
                    for key, value in item_dict.items():
                        if value:  # Only update non-empty values
                            setattr(existing, key, value)
                    
                    existing.scrape_log = self.scrape_log
                    existing.save()
                    updated += 1
                    
                    logger.debug(f"Updated: {item.title[:50]}")
                else:
                    # Create new
                    item_data = item.to_dict()
                    if 'url' in item_data and 'source_url' not in item_data:
                        item_data['source_url'] = item_data.pop('url')
                        
                    ScrapedContent.objects.create(
                        scraper_config=self.config,
                        scrape_log=self.scrape_log,
                        **item_data
                    )
                    saved += 1
                    
                    logger.debug(f"Saved: {item.title[:50]}")
                    
            except Exception as e:
                logger.error(f"Failed to save item: {e}", exc_info=True)
                skipped += 1
                if self.scrape_log:
                    self.scrape_log.items_failed += 1
                    self.scrape_log.save()
        
        return saved, updated, skipped

    def crawl(self, query: str = None, test_mode: bool = False) -> Dict[str, Any]:
        """
        Execute multi-stage crawling using GenericCrawlerService
        """
        from .generic_crawler import GenericCrawlerService
        
        crawler = GenericCrawlerService(self.config)
        result = crawler.crawl(query=query, test_mode=test_mode)
        
        if not result.get('success'):
            return result
            
        # If not test mode, the items are already handled (orchestrator called scrape internally)
        # Note: GenericCrawlerService calls self.orchestrator.scrape() for each link.
        
        return {
            'success': True,
            'items': result.get('items', [])[:10], # Return samples
            'total_found': result.get('stats', {}).get('items_extracted', 0),
            'stats': result.get('stats'),
            'test_mode': test_mode
        }
    
    def _update_config_statistics(self, success: bool, items_count: int = 0, error: str = None):
        """Update scraper config statistics"""
        self.config.last_run = timezone.now()
        
        if hasattr(self.config, 'calculate_next_run'):
            self.config.next_run = self.config.calculate_next_run()
        else:
            hours = getattr(self.config, 'scrape_interval_hours', 24)
            self.config.next_run = timezone.now() + timedelta(hours=hours)
        
        if hasattr(self.config, 'update_statistics'):
            if success:
                self.config.update_statistics(success=True, items_count=items_count)
            else:
                self.config.update_statistics(success=False)
        else:
            if success:
                self.config.total_items_scraped = getattr(self.config, 'total_items_scraped', 0) + items_count
                current_rate = getattr(self.config, 'success_rate', 0.0)
                self.config.success_rate = (current_rate * 9 + 100) / 10 if current_rate else 100.0
            else:
                current_rate = getattr(self.config, 'success_rate', 0.0)
                self.config.success_rate = (current_rate * 9) / 10 if current_rate else 0.0
                
        if not success and error:
            if hasattr(self.config, 'last_error'):
                self.config.last_error = error
            if hasattr(self.config, 'last_error_at'):
                self.config.last_error_at = timezone.now()
        
        self.config.save()
    
    @staticmethod
    def scrape_all_active(triggered_by: str = 'scheduled') -> List[Dict[str, Any]]:
        """
        Scrape all active scrapers
        
        Returns:
            List of results for each scraper
        """
        from ..models import ScraperConfig
        
        results = []
        
        active_configs = ScraperConfig.objects.filter(is_active=True)
        
        for config in active_configs:
            # Check if should run now
            should_run = False
            if hasattr(config, 'should_run_now'):
                should_run = config.should_run_now()
            else:
                should_run = not config.next_run or config.next_run <= timezone.now()
                
            if not should_run:
                logger.info(f"Skipping {config.name} (not scheduled yet)")
                continue
            
            try:
                orchestrator = ScraperOrchestrator(config)
                result = orchestrator.scrape(triggered_by=triggered_by)
                results.append({
                    'scraper': config.name,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Failed to scrape {config.name}: {e}")
                results.append({
                    'scraper': config.name,
                    'result': {
                        'success': False,
                        'error': str(e)
                    }
                })
        
        return results
    
    @staticmethod
    def scrape_by_id(config_id: int, query: str = None, 
                     max_results: int = None, triggered_by: str = 'manual') -> Dict[str, Any]:
        """
        Scrape specific scraper by ID
        
        Args:
            config_id: ScraperConfig ID
            query: Search query
            max_results: Max results
            triggered_by: Trigger source
            
        Returns:
            Scraping result
        """
        from ..models import ScraperConfig
        
        try:
            config = ScraperConfig.objects.get(id=config_id)
            orchestrator = ScraperOrchestrator(config)
            return orchestrator.scrape(query, max_results, triggered_by)
        except ScraperConfig.DoesNotExist:
            return {
                'success': False,
                'error': f'Scraper config {config_id} not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
