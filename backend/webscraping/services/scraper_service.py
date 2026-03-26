"""
Scraper Service - Unified entry point for all scraping operations.
Delegates to ScraperOrchestrator for actual execution.
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def scrape_from_source(config_id: int, query: str = None, max_results: int = None) -> Dict:
    """
    Scrape from a specific source by config ID.
    Used by admin "Run Now" action and API endpoints.
    
    Args:
        config_id: ScraperConfig ID
        query: Search query (overrides config default)
        max_results: Max results (overrides config default)
    
    Returns:
        {
            'success': bool,
            'items': list,
            'total_found': int,
            'saved': int,
            'updated': int,
            'skipped': int,
            'duration': float,
            'error': str (if failed)
        }
    """
    from ..models import ScraperConfig
    from .scraper_orchestrator import ScraperOrchestrator

    try:
        config = ScraperConfig.objects.get(id=config_id)
        if not config.is_active:
            return {'success': False, 'error': 'Bu kaynak aktif değil'}

        orchestrator = ScraperOrchestrator(config)
        result = orchestrator.scrape(
            query=query,
            max_results=max_results,
            triggered_by='manual'
        )

        # Ensure backward compatibility for frontend expectations
        if 'total_found' not in result:
            result['total_found'] = result.get('saved', 0) + result.get('updated', 0) + result.get('skipped', 0)
        return result

    except ScraperConfig.DoesNotExist:
        return {'success': False, 'error': 'Kaynak bulunamadı'}
    except Exception as e:
        logger.error(f"scrape_from_source failed for config {config_id}: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def scrape_all_active_sources() -> List[Dict]:
    """
    Scrape all active sources.
    Used by admin bulk action and scheduled tasks.
    """
    from ..models import ScraperConfig

    results = []
    active_configs = ScraperConfig.objects.filter(is_active=True)

    for config in active_configs:
        result = scrape_from_source(config.id)
        results.append({
            'source': config.name,
            'result': result
        })

    return results
