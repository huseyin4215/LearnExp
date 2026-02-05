from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def scrape(self):
        """
        Scrape content from the source.
        Returns: List of dictionaries containing scraped data
        """
        pass
    
    @abstractmethod
    def parse(self, raw_data):
        """
        Parse raw scraped data into standardized format.
        Returns: Dictionary with standardized fields
        """
        pass
    
    def save_results(self, results):
        """
        Save scraped results to database.
        Returns: Number of items successfully saved
        """
        from ..models import ScrapedContent
        
        saved_count = 0
        for item_data in results:
            try:
                parsed = self.parse(item_data)
                
                # Create or update content
                ScrapedContent.objects.update_or_create(
                    external_id=parsed['external_id'],
                    defaults={
                        'scraper_config': self.config,
                        'title': parsed['title'],
                        'description': parsed['description'],
                        'authors': parsed['authors'],
                        'source': parsed['source'],
                        'published_date': parsed.get('published_date'),
                        'url': parsed['url'],
                        'content_type': parsed['content_type'],
                        'tags': parsed.get('tags', []),
                        'raw_data': item_data,
                        'location': parsed.get('location', ''),
                        'deadline': parsed.get('deadline'),
                        'amount': parsed.get('amount', ''),
                    }
                )
                saved_count += 1
            except Exception as e:
                # Log error but continue processing
                print(f"Error saving item: {e}")
                continue
        
        return saved_count
