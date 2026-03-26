"""
Diagnose Scraper Configurations

Usage:
    python manage.py diagnose_scraper --all
    python manage.py diagnose_scraper --name "Ankara University News"
    python manage.py diagnose_scraper --id 1

Checks:
    - HTTP connectivity
    - Content length & SPA detection
    - Selector matching
    - Saves HTML snapshots for debugging
"""
import os
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Diagnose scraper configurations: check connectivity, selectors, and SPA detection'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Diagnose all active scrapers')
        parser.add_argument('--name', type=str, help='Diagnose scraper by name')
        parser.add_argument('--id', type=int, help='Diagnose scraper by ID')
        parser.add_argument('--save-html', action='store_true', default=True,
                            help='Save HTML snapshots to logs/ (default: True)')

    def handle(self, *args, **options):
        from webscraping.models import ScraperConfig

        configs = []

        if options['all']:
            configs = list(ScraperConfig.objects.filter(is_active=True))
        elif options['name']:
            configs = list(ScraperConfig.objects.filter(name__icontains=options['name']))
        elif options['id']:
            try:
                configs = [ScraperConfig.objects.get(id=options['id'])]
            except ScraperConfig.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Scraper with ID {options['id']} not found"))
                return
        else:
            self.stderr.write(self.style.WARNING('Specify --all, --name, or --id'))
            return

        if not configs:
            self.stderr.write(self.style.WARNING('No scraper configurations found'))
            return

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"  SCRAPER DIAGNOSTICS — {len(configs)} config(s)")
        self.stdout.write(f"{'='*70}\n")

        for config in configs:
            self._diagnose_config(config, save_html=options['save_html'])

    def _diagnose_config(self, config, save_html=True):
        import requests
        from bs4 import BeautifulSoup

        self.stdout.write(f"\n{'─'*60}")
        self.stdout.write(self.style.HTTP_INFO(f"  {config.name}"))
        self.stdout.write(f"{'─'*60}")
        self.stdout.write(f"  Source type:  {config.source_type}")
        self.stdout.write(f"  Scraper type: {config.scraper_type}")
        self.stdout.write(f"  Base URL:     {config.base_url}")
        self.stdout.write(f"  Active:       {config.is_active}")

        # 1. Check HTTP connectivity
        self.stdout.write(f"\n  [1] HTTP Connectivity")
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': config.user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            })
            response = session.get(
                config.base_url,
                timeout=config.timeout_seconds,
                verify=getattr(config, 'verify_ssl', True),
                allow_redirects=True,
            )
            self.stdout.write(self.style.SUCCESS(
                f"      ✓ Status: {response.status_code} | "
                f"Size: {len(response.content):,} bytes | "
                f"Content-Type: {response.headers.get('content-type', 'N/A')}"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"      ✗ Connection failed: {e}"))
            return

        # 2. Parse and analyze content
        self.stdout.write(f"\n  [2] Content Analysis")
        soup = BeautifulSoup(response.content, 'lxml')
        body = soup.find('body')
        body_text = body.get_text(strip=True) if body else ''
        body_text_len = len(body_text)

        self.stdout.write(f"      Body text length: {body_text_len:,} chars")

        # SPA detection heuristic
        is_spa = False
        spa_indicators = []

        if body_text_len < 200:
            is_spa = True
            spa_indicators.append(f"Very short body text ({body_text_len} chars)")

        # Check for common SPA frameworks
        html_str = str(soup)
        for fw_marker, fw_name in [
            ('ng-app', 'Angular'),
            ('data-critters-container', 'Angular (Critters)'),
            ('__next', 'Next.js'),
            ('__nuxt', 'Nuxt.js'),
            ('data-reactroot', 'React'),
            ('id="app"', 'Vue.js'),
        ]:
            if fw_marker in html_str:
                is_spa = True
                spa_indicators.append(f"{fw_name} markers detected")

        if is_spa:
            self.stdout.write(self.style.WARNING(
                f"      ⚠ SPA DETECTED: {', '.join(spa_indicators)}"
            ))
            if config.scraper_type == 'html':
                self.stdout.write(self.style.ERROR(
                    f"      ✗ PROBLEM: scraper_type='html' cannot scrape SPA pages!\n"
                    f"        → Change scraper_type to 'selenium' or 'playwright' in Admin"
                ))
        else:
            self.stdout.write(self.style.SUCCESS(f"      ✓ Static HTML page (no SPA detected)"))

        # 3. Test selectors
        self.stdout.write(f"\n  [3] Selector Testing")
        selectors = config.selectors or {}

        if not selectors:
            self.stdout.write(self.style.WARNING(f"      ⚠ No selectors configured"))
        else:
            container_sel = selectors.get('item_container', 'article')
            self.stdout.write(f"      Container selector: {container_sel}")

            try:
                items = soup.select(container_sel)
                if items:
                    self.stdout.write(self.style.SUCCESS(
                        f"      ✓ Found {len(items)} items with container selector"
                    ))
                    # Test sub-selectors on first item
                    first_item = items[0]
                    for field_name, field_config in selectors.items():
                        if field_name in ('item_container', 'pagination_next'):
                            continue
                        sel = field_config if isinstance(field_config, str) else field_config.get('selector', '')
                        if sel:
                            match = first_item.select_one(sel)
                            status = self.style.SUCCESS('✓') if match else self.style.ERROR('✗')
                            value = ''
                            if match:
                                value = f' → "{match.get_text(strip=True)[:60]}"'
                            self.stdout.write(f"        {status} {field_name}: {sel}{value}")
                else:
                    self.stdout.write(self.style.ERROR(
                        f"      ✗ 0 items found with '{container_sel}'"
                    ))
                    # Suggest alternatives
                    for alt_sel in ['article', '.card', '.item', '.post', '.entry', 'li', '.result']:
                        alt_items = soup.select(alt_sel)
                        if alt_items:
                            self.stdout.write(self.style.WARNING(
                                f"        → Try '{alt_sel}' ({len(alt_items)} matches)"
                            ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"      ✗ Selector error: {e}"))

        # 4. Save HTML snapshot
        if save_html:
            self.stdout.write(f"\n  [4] HTML Snapshot")
            logs_dir = os.path.join(settings.BASE_DIR, 'logs', 'html_snapshots')
            os.makedirs(logs_dir, exist_ok=True)
            safe_name = config.name.replace(' ', '_').replace('/', '_')[:50]
            filepath = os.path.join(logs_dir, f'{safe_name}.html')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()[:50000]))
            self.stdout.write(self.style.SUCCESS(f"      ✓ Saved to {filepath}"))

        # Summary
        self.stdout.write(f"\n  {'─'*56}")
        if is_spa and config.scraper_type == 'html':
            self.stdout.write(self.style.ERROR(
                f"  VERDICT: ✗ WILL FAIL — SPA page + html engine\n"
                f"  FIX: Change scraper_type to 'selenium' in Admin"
            ))
        elif not selectors:
            self.stdout.write(self.style.WARNING(
                f"  VERDICT: ⚠ NEEDS CONFIG — No selectors defined"
            ))
        elif len(soup.select(selectors.get('item_container', 'article'))) == 0:
            self.stdout.write(self.style.WARNING(
                f"  VERDICT: ⚠ SELECTORS MISS — Container selector matches nothing"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"  VERDICT: ✓ LOOKS GOOD — Connectivity OK, selectors match"
            ))
        self.stdout.write('')
