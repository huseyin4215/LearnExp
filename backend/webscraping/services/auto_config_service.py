import logging
import json
import time
import urllib.parse
from playwright.sync_api import sync_playwright, Page
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AutoConfigService:
    """
    AI-Powered Scraping Architect & Configuration Generator.
    Automatically detects rendering, structure, pagination, and crawling needs.
    """
    
    def __init__(self, url: str):
        self.url = url
        self.render_mode = "static"
        self.scraper_type = "html"
        
    def detect_selectors(self) -> Dict[str, Any]:
        """
        Complete analysis of the webpage to generate a full scraping config.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Set a common user agent
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                logger.info(f"Architect: Analyzing {self.url}...")
                
                # 1. Rendering Detection (Initial vs Final)
                # Load with minimal wait first
                response = page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                initial_content_len = len(page.content())
                
                # Full wait
                page.wait_for_load_state("networkidle")
                time.sleep(2) # Extra buffer for SPAs
                final_content_len = len(page.content())
                
                # Heuristic for JS rendering necessity
                if final_content_len > initial_content_len * 1.5 or page.query_selector('div:empty'):
                    self.render_mode = "dynamic"
                    self.scraper_type = "playwright"
                else:
                    self.render_mode = "static"
                    self.scraper_type = "html"
                
                # 2. Structure & Stage 1 Discovery
                analysis = self._run_dom_analysis(page)
                if not analysis:
                    return {"success": False, "error": "Could not identify repeating patterns/items on this page."}
                
                # 3. Pagination Strategy
                pagination = self._detect_pagination(page)
                
                # 4. Multi-Step (Stage 2) Analysis
                multi_step_config = self._analyze_multi_step(page, analysis, context)
                
                # 5. Full Config Assembly
                config = self._assemble_config(analysis, pagination, multi_step_config)
                
                # 6. Preview Extraction
                preview_items = self._get_preview_items(page, analysis)
                
                browser.close()
                
                return {
                    "success": True,
                    "config": config,
                    "strategy_explanation": self._generate_explanation(config),
                    "items": preview_items,
                    "debug": {
                        "render_mode": self.render_mode,
                        "content_growth": f"{(final_content_len/initial_content_len - 1)*100:.1f}%" if initial_content_len else "N/A"
                    }
                }
                
        except Exception as e:
            logger.error(f"Scraping Architect failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _run_dom_analysis(self, page: Page) -> Optional[Dict[str, Any]]:
        """JS-based DOM pattern recognition"""
        return page.evaluate('''() => {
            const findItemContainers = () => {
                const classCounts = {};
                const all = document.querySelectorAll('body *');
                
                all.forEach(el => {
                    if (el.classList.length > 0 && el.offsetHeight > 40) {
                        const classStr = Array.from(el.classList).join('.');
                        classCounts[classStr] = (classCounts[classStr] || 0) + 1;
                    }
                });
                
                return Object.entries(classCounts)
                    .filter(([cls, count]) => count >= 3 && count <= 60)
                    .sort((a, b) => b[1] - a[1])
                    .map(([cls, count]) => ({ selector: '.' + cls.split('.').join('.'), count }));
            };
            
            const extractSelectors = (containerSel) => {
                const container = document.querySelector(containerSel);
                if (!container) return null;
                
                const res = { item_container: containerSel };
                
                // Title & URL
                const a = container.querySelector('a[href]');
                if (a) {
                    res.title = 'a';
                    res.url = 'a';
                }
                
                // Image
                const img = container.querySelector('img');
                if (img) res.image = 'img';
                
                // Description/Abstract
                const p = container.querySelector('p, .description, .summary, .abstract');
                if (p) res.abstract = p.className ? '.' + p.className.split(' ')[0] : p.tagName.toLowerCase();
                
                return res;
            };

            const containers = findItemContainers();
            if (containers.length === 0) return null;
            
            return {
                winner: containers[0],
                selectors: extractSelectors(containers[0].selector)
            };
        }''')

    def _detect_pagination(self, page: Page) -> Dict[str, Any]:
        """Identifies how to move to next pages"""
        return page.evaluate('''() => {
            const res = { type: 'NONE', template: '', selector: '' };
            
            // 1. Check for 'Next' button
            const nextWords = ['Next', 'Sonraki', '>', '»', 'arrow-right'];
            const nextBtn = Array.from(document.querySelectorAll('a, button')).find(el => 
                nextWords.some(w => el.innerText.includes(w) || el.className.includes(w) || (el.getAttribute('aria-label') || '').includes(w))
            );
            
            if (nextBtn) {
                res.type = 'NEXT_BUTTON';
                res.selector = nextBtn.className ? '.' + nextBtn.className.split(' ')[0] : 'a:contains("Next")';
                return res;
            }
            
            // 2. Check for URL numbers (URL_INCREMENT/QUERY_PARAM)
            const url = window.location.href;
            if (url.includes('page=') || url.includes('p=')) {
                res.type = 'QUERY_PARAM';
                res.template = url.replace(/([?&](page|p)=)\d+/, '$1{page}');
                return res;
            }
            
            // 3. Infinite Scroll Check (Handled in assembling via Python scroll detection)
            return res;
        }''')

    def _analyze_multi_step(self, page: Page, analysis: Dict[str, Any], context) -> Dict[str, Any]:
        """Checks if Stage 2 (Detail pages) is needed and discoverable"""
        res = {"enabled": False, "step2_selectors": {}}
        
        selectors = analysis.get('selectors', {})
        if not selectors.get('url'):
            return res
            
        try:
            # Try to get one sample link
            container_sel = selectors['item_container']
            url_sel = selectors['url']
            
            sample_el = page.query_selector(f"{container_sel} {url_sel}")
            if not sample_el:
                return res
                
            sample_url = urllib.parse.urljoin(self.url, sample_el.get_attribute('href'))
            if sample_url == self.url or '#' in sample_url:
                return res
            
            # Switch to Stage 2: Visit detail page
            res["enabled"] = True
            logger.info(f"Architect: Testing Stage 2 on {sample_url}")
            
            detail_page = context.new_page()
            detail_page.goto(sample_url, wait_until="domcontentloaded")
            time.sleep(2)
            
            # Detect detail page fields
            stage2 = detail_page.evaluate('''() => {
                const res = {};
                // H1 is almost always the title
                const h1 = document.querySelector('h1');
                if (h1) res.title = 'h1';
                
                // Date discovery
                const dateTags = document.querySelectorAll('span, time, .date, .meta, .published');
                for (let tag of dateTags) {
                    if (/\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4}/.test(tag.innerText)) {
                        res.published_date = '.' + (tag.className ? tag.className.split(' ')[0] : tag.tagName.toLowerCase());
                        break;
                    }
                }
                
                // Main content
                const main = document.querySelector('article, main, .content, .post-content, #content');
                if (main) res.abstract = main.tagName.toLowerCase() + (main.className ? '.' + main.className.split(' ')[0] : '');
                
                return res;
            }''')
            
            res["step2_selectors"] = stage2
            detail_page.close()
            
        except Exception as e:
            logger.warning(f"Stage 2 analysis failed: {e}")
            
        return res

    def _assemble_config(self, analysis: Dict[str, Any], pagination: Dict[str, Any], multi_step: Dict[str, Any]) -> Dict[str, Any]:
        """Creates the final configuration object"""
        selectors = analysis.get('selectors', {})
        
        config = {
            "name": f"AutoDetected_{urllib.parse.urlparse(self.url).netloc.replace('.', '_')}",
            "scraper_type": self.scraper_type,
            "render_mode": self.render_mode,
            "base_url": self.url,
            "selectors": selectors,
            "pagination": {
                "type": pagination.get('type', 'NONE'),
                "template": pagination.get('template', ''),
                "selector": pagination.get('selector', ''),
                "start_page": 1
            },
            "advanced": {
                "enable_multi_step": multi_step.get('enabled', False),
                "enable_query_encoding": False, # Dynamic guess later
                "enable_relative_url_fix": True,
                "max_depth": 1 if multi_step.get('enabled') else 0
            },
            "scroll": {
                "enabled": self.render_mode == "dynamic",
                "count": 5,
                "delay": 2000
            }
        }
        
        if multi_step.get('enabled'):
            config["step1_selectors"] = selectors
            config["step2_selectors"] = multi_step["step2_selectors"]
            
        return config

    def _get_preview_items(self, page: Page, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts sample data for real-time validation"""
        items = []
        selectors = analysis.get('selectors', {})
        container = selectors.get('item_container')
        
        if not container:
            return items
            
        try:
            elements = page.query_selector_all(container)[:3]
            for el in elements:
                item = {}
                for field, sel in selectors.items():
                    if field in ('item_container', 'pagination_next'): continue
                    
                    found = el.query_selector(sel)
                    if found:
                        if field == 'url':
                            item['source_url'] = urllib.parse.urljoin(self.url, found.get_attribute('href'))
                        elif field == 'image':
                            item['image_url'] = urllib.parse.urljoin(self.url, found.get_attribute('src') or found.get_attribute('data-src') or "")
                        else:
                            item[field] = found.inner_text().strip()
                
                if item:
                    items.append(item)
        except Exception as e:
            logger.warning(f"Preview extraction failed: {e}")
            
        return items

    def _generate_explanation(self, config: Dict[str, Any]) -> str:
        """Explains why this strategy was chosen"""
        exp = []
        if config['render_mode'] == 'dynamic':
            exp.append("Page identified as dynamic (JavaScript/SPA) based on DOM growth analysis.")
        else:
            exp.append("Static page detected; using fast HTML parsing.")
            
        if config['advanced']['enable_multi_step']:
            exp.append("Multi-stage crawling enabled: Stage 1 will discover links, Stage 2 will extract detailed content.")
            
        pagination_type = config['pagination']['type']
        if pagination_type != 'NONE':
            exp.append(f"Pagination strategy: {pagination_type} ({config['pagination'].get('selector') or config['pagination'].get('template')})")
            
        return " ".join(exp)

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.ankara.edu.tr/kategori/duyurular/"
    svc = AutoConfigService(url)
    print(json.dumps(svc.detect_selectors(), indent=2))
