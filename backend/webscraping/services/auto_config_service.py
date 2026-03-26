import logging
import json
import time
from collections import Counter
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class AutoConfigService:
    """
    Automated selector detection using Playwright
    """
    
    def __init__(self, url):
        self.url = url
        self._browser = None
        self._context = None
        self._page = None
        
    def detect_selectors(self):
        """
        Analyzes the page and returns suggested selectors
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                logger.info(f"Auto-Config: Loading {self.url}...")
                # Use networkidle and wait for body
                page.goto(self.url, wait_until="networkidle", timeout=30000)
                page.wait_for_selector("body")
                
                # Wait a bit for extra JS/SPAs
                time.sleep(3)
                
                # --- Advanced Detection Logic ---
                analysis = page.evaluate('''() => {
                    const findMostRepeatedContainer = () => {
                        const allElements = document.querySelectorAll('body *');
                        const classCounts = {};
                        
                        allElements.forEach(el => {
                            if (el.classList.length > 0 && el.offsetHeight > 20) {
                                const classStr = Array.from(el.classList).join('.');
                                classCounts[classStr] = (classCounts[classStr] || 0) + 1;
                            }
                        });
                        
                        // Sort by frequency and filter reasonable counts (e.g. 4-40)
                        return Object.entries(classCounts)
                            .filter(([cls, count]) => count >= 3 && count <= 50)
                            .sort((a, b) => b[1] - a[1])
                            .map(([cls, count]) => ({ selector: '.' + cls.split('.').join('.'), count }));
                    };
                    
                    const detectFields = (containerSelector) => {
                        const container = document.querySelector(containerSelector);
                        if (!container) return {};
                        
                        const res = {};
                        
                        // 1. Title & URL (Find <a> inside <h3>, <h2> or with 'title' in class)
                        const anchors = Array.from(container.querySelectorAll('a[href]'));
                        let bestAnchor = anchors.find(a => /h[1-4]/i.test(a.parentElement.tagName) || /title/i.test(a.className));
                        if (!bestAnchor && anchors.length > 0) bestAnchor = anchors[0];
                        
                        if (bestAnchor) {
                            res.url = 'a';
                            res.title = 'a'; // Refine if text is empty?
                        }
                        
                        // 2. Image
                        const img = container.querySelector('img');
                        if (img) res.image = 'img';
                        
                        // 3. Date
                        const dateTags = container.querySelectorAll('span, p, time, .date, .meta');
                        for (let tag of dateTags) {
                            if (/\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4}/.test(tag.innerText)) {
                                res.published_date = '.' + (tag.className ? tag.className.split(' ')[0] : tag.tagName.toLowerCase());
                                break;
                            }
                        }
                        
                        return res;
                    };
                    
                    const detectPagination = () => {
                        const nextBtn = document.querySelector('a[href*="page="], a[href*="p="], .next, .pagination-next');
                        if (nextBtn) return '.next'; // Simplification
                        return null;
                    };

                    const containers = findMostRepeatedContainer();
                    if (containers.length === 0) return null;
                    
                    const winner = containers[0];
                    const fields = detectFields(winner.selector);
                    
                    return {
                        selectors: { item_container: winner.selector, ...fields },
                        pagination: detectPagination(),
                        debug: { 
                            containers_found: containers.length,
                            items_detected: winner.count
                        }
                    };
                }''')
                
                if not analysis:
                    return {"success": False, "error": "Could not detect repeated patterns on this page."}
                
                # Extract preview items (first 3)
                preview_items = []
                try:
                    # Very simple extraction for preview
                    # In a real scenario, we'd use the discovered selectors to actually scrape
                    selectors = analysis['selectors']
                    container = selectors['item_container']
                    title_sel = selectors.get('title', 'a')
                    url_sel = selectors.get('url', 'a')
                    img_sel = selectors.get('image', 'img')
                    
                    elements = page.query_selector_all(container)[:3]
                    for el in elements:
                        title_el = el.query_selector(title_sel)
                        url_el = el.query_selector(url_sel)
                        img_el = el.query_selector(img_sel)
                        
                        preview_items.append({
                            "title": title_el.inner_text() if title_el else "N/A",
                            "source_url": urljoin(self.url, url_el.get_attribute('href')) if url_el else self.url,
                            "image_url": urljoin(self.url, img_el.get_attribute('src')) if img_el else ""
                        })
                except Exception as e:
                    logger.warning(f"Preview extraction failed: {e}")
                
                return {
                    "success": True,
                    "selectors": analysis['selectors'],
                    "items": preview_items,
                    "debug": analysis['debug'],
                    "pagination": analysis['pagination']
                }
                
        except Exception as e:
            logger.error(f"Auto-config failed: {e}")
            return {"success": False, "error": str(e)}
                
        except Exception as e:
            logger.error(f"Auto-config failed: {e}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test
    svc = AutoConfigService("https://www.ankara.edu.tr/kategori/duyurular/")
    print(json.dumps(svc.detect_selectors(), indent=2))
