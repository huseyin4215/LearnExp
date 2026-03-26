"""
Universal Date Parser
Handles multiple date formats with auto-detection
"""
from datetime import datetime, date
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


class DateParser:
    """
    Robust date parser supporting multiple formats
    """
    
    # Common date formats
    DATE_FORMATS = [
        # ISO formats
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S',
        
        # US formats
        '%m/%d/%Y',
        '%m-%d-%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%B %d %Y',
        '%b %d %Y',
        
        # European formats
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d.%m.%Y',
        '%d %B %Y',
        '%d %b %Y',
        
        # RFC formats
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        
        # Other common formats
        '%Y/%m/%d',
        '%d.%m.%y',
        '%d/%m/%y',
        '%m/%d/%y',
        '%Y',  # Year only
    ]
    
    # Month name mappings (for non-English months)
    MONTH_NAMES = {
        # Turkish
        'ocak': 'january', 'şubat': 'february', 'mart': 'march',
        'nisan': 'april', 'mayıs': 'may', 'haziran': 'june',
        'temmuz': 'july', 'ağustos': 'august', 'eylül': 'september',
        'ekim': 'october', 'kasım': 'november', 'aralık': 'december',
        
        # Spanish
        'enero': 'january', 'febrero': 'february', 'marzo': 'march',
        'abril': 'april', 'mayo': 'may', 'junio': 'june',
        'julio': 'july', 'agosto': 'august', 'septiembre': 'september',
        'octubre': 'october', 'noviembre': 'november', 'diciembre': 'december',
        
        # French
        'janvier': 'january', 'février': 'february', 'mars': 'march',
        'avril': 'april', 'mai': 'may', 'juin': 'june',
        'juillet': 'july', 'août': 'august', 'septembre': 'september',
        'octobre': 'october', 'novembre': 'november', 'décembre': 'december',
        
        # German
        'januar': 'january', 'februar': 'february', 'märz': 'march',
        'april': 'april', 'mai': 'may', 'juni': 'june',
        'juli': 'july', 'august': 'august', 'september': 'september',
        'oktober': 'october', 'november': 'november', 'dezember': 'december',
    }
    
    def __init__(self, custom_format: str = None):
        """
        Args:
            custom_format: Custom date format (Python strftime)
        """
        self.custom_format = custom_format
    
    def parse(self, date_string: str) -> Optional[date]:
        """
        Parse date string to date object
        
        Args:
            date_string: Date string in any common format
            
        Returns:
            date object or None if parsing fails
        """
        if not date_string:
            return None
        
        # Clean the string
        date_string = str(date_string).strip()
        
        if not date_string:
            return None
        
        # Try custom format first
        if self.custom_format:
            try:
                return datetime.strptime(date_string, self.custom_format).date()
            except ValueError:
                pass
        
        # Normalize month names
        normalized = self._normalize_month_names(date_string)
        
        # Try all formats
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(normalized, fmt)
                return parsed.date()
            except ValueError:
                continue
        
        # Try regex extraction
        extracted_date = self._extract_date_regex(date_string)
        if extracted_date:
            return extracted_date
        
        # Try relative dates
        relative_date = self._parse_relative_date(date_string)
        if relative_date:
            return relative_date
        
        logger.warning(f"Could not parse date: {date_string}")
        return None
    
    def _normalize_month_names(self, date_string: str) -> str:
        """
        Convert non-English month names to English
        """
        lower = date_string.lower()
        
        for foreign, english in self.MONTH_NAMES.items():
            if foreign in lower:
                # Replace with English month name
                lower = lower.replace(foreign, english)
                # Capitalize first letter
                return lower.replace(english, english.capitalize())
        
        return date_string
    
    def _extract_date_regex(self, date_string: str) -> Optional[date]:
        """
        Extract date using regex patterns
        """
        patterns = [
            # YYYY-MM-DD
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            # DD/MM/YYYY
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),
            # MM/DD/YYYY
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),
            # YYYY only
            (r'\b(19|20)\d{2}\b', '%Y'),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, date_string)
            if match:
                try:
                    if fmt == '%Y':
                        # Year only
                        year = int(match.group(0))
                        return date(year, 1, 1)
                    else:
                        return datetime.strptime(match.group(0), fmt).date()
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _parse_relative_date(self, date_string: str) -> Optional[date]:
        """
        Parse relative dates like "2 days ago", "yesterday", "today"
        """
        from datetime import timedelta
        
        lower = date_string.lower()
        today = date.today()
        
        if 'today' in lower or 'bugün' in lower:
            return today
        
        if 'yesterday' in lower or 'dün' in lower:
            return today - timedelta(days=1)
        
        # "X days ago" pattern
        match = re.search(r'(\d+)\s*(day|days|gün)\s*ago', lower)
        if match:
            days = int(match.group(1))
            return today - timedelta(days=days)
        
        # "X weeks ago"
        match = re.search(r'(\d+)\s*(week|weeks|hafta)\s*ago', lower)
        if match:
            weeks = int(match.group(1))
            return today - timedelta(weeks=weeks)
        
        # "X months ago"
        match = re.search(r'(\d+)\s*(month|months|ay)\s*ago', lower)
        if match:
            months = int(match.group(1))
            return today - timedelta(days=months * 30)  # Approximate
        
        return None
    
    def parse_date_range(self, start_str: str, end_str: str) -> tuple:
        """
        Parse date range
        
        Returns:
            (start_date, end_date) tuple
        """
        start = self.parse(start_str) if start_str else None
        end = self.parse(end_str) if end_str else None
        return start, end
    
    def is_valid_date(self, date_string: str) -> bool:
        """
        Check if string is a valid date
        """
        return self.parse(date_string) is not None
