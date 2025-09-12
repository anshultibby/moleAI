"""Direct HTTP scraper module with intelligent JavaScript support"""

import os
import re
import asyncio
import requests
import hashlib
from typing import Dict, Any, Optional, List
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from app.models.resource import Resource, ResourceMetadata

# Try to import playwright for JS rendering
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("playwright not available, JavaScript rendering will be disabled")

# Fallback to requests-html if playwright not available
try:
    from requests_html import AsyncHTMLSession
    REQUESTS_HTML_AVAILABLE = True
except ImportError:
    REQUESTS_HTML_AVAILABLE = False
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Neither playwright nor requests-html available, JavaScript rendering will be disabled")


class DirectScraperError(Exception):
    """Custom exception for direct scraper-related errors"""
    pass

# Keep old name for backward compatibility
ScrapingBeeError = DirectScraperError


def _needs_javascript_rendering(html_content: str, url: str) -> bool:
    """
    Intelligently determine if a page needs JavaScript rendering
    by analyzing the static HTML content.
    """
    if not html_content or len(html_content.strip()) < 100:
        return True  # Very little content, might need JS
    
    # Check for common indicators that JS is needed
    js_indicators = [
        # React/Vue/Angular apps
        r'<div[^>]*id=["\']root["\']',
        r'<div[^>]*id=["\']app["\']',
        r'<div[^>]*id=["\']__next["\']',
        r'data-reactroot',
        r'ng-app',
        r'v-app',
        
        # Common JS frameworks
        r'React\.',
        r'Vue\.',
        r'angular\.',
        
        # Loading indicators
        r'loading',
        r'spinner',
        r'skeleton',
        
        # Empty content containers
        r'<div[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>\s*</div>',
        r'<main[^>]*>\s*</main>',
        
        # AJAX/fetch indicators
        r'fetch\(',
        r'XMLHttpRequest',
        r'\.ajax\(',
    ]
    
    # Check for JS indicators
    for pattern in js_indicators:
        if re.search(pattern, html_content, re.IGNORECASE):
            return True
    
    # Check content density - if very low, might need JS
    text_content = re.sub(r'<[^>]+>', '', html_content)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # If we have very little actual text content, probably need JS
    if len(text_content) < 200:
        return True
    
    # Check for specific domains that are known to be JS-heavy
    js_heavy_domains = [
        'amazon.com', 'ebay.com', 'etsy.com', 'shopify.com',
        'facebook.com', 'twitter.com', 'instagram.com',
        'youtube.com', 'netflix.com', 'spotify.com'
    ]
    
    for domain in js_heavy_domains:
        if domain in url.lower():
            return True
    
    return False


class DirectScraper:
    """Direct HTTP scraper with JavaScript support"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize direct HTTP scraper
        
        Args:
            api_key: Not used anymore, kept for backward compatibility
        """
        # Keep the same interface but don't require API key anymore
        self.timeout = 30
        self.session = requests.Session()
        
        # Set up common headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Initialize HTML session for JavaScript rendering if available (fallback)
        if REQUESTS_HTML_AVAILABLE:
            self.html_session = AsyncHTMLSession()
            self.html_session.headers.update(self.session.headers)
        
        # Playwright browser instance (lazy initialization)
        self._playwright = None
        self._browser = None
    
    async def _get_browser(self):
        """Lazy initialization of Playwright browser"""
        if not PLAYWRIGHT_AVAILABLE:
            return None
            
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                ]
            )
        return self._browser
    
    async def _render_with_playwright(self, url: str, wait: int = 1000) -> str:
        """Render page with Playwright (faster than requests-html)"""
        browser = await self._get_browser()
        if not browser:
            raise Exception("Playwright not available")
        
        context = await browser.new_context(
            user_agent=self.session.headers['User-Agent'],
            viewport={'width': 1280, 'height': 720}
        )
        
        try:
            page = await context.new_page()
            
            # Block unnecessary resources for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf,eot}", lambda route: route.abort())
            
            # Navigate to page
            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
            
            # Smart waiting - wait for network idle or specific time, whichever is shorter
            try:
                await page.wait_for_load_state('networkidle', timeout=min(wait, 3000))
            except:
                # If network idle times out, just wait the specified time
                await page.wait_for_timeout(min(wait, 1000))
            
            content = await page.content()
            return content
            
        finally:
            await context.close()
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self._browser:
            try:
                await self._browser.close()
            except:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except:
                pass
    
    async def scrape_url(
        self, 
        url: str, 
        render_js: bool = True,
        wait: int = 1000,
        wait_for: Optional[str] = None,
        screenshot: bool = False,
        extract_rules: Optional[Dict] = None,
        smart_js_detection: bool = True
    ) -> Resource:
        """
        Scrape content from a single URL with intelligent JavaScript detection
        
        Args:
            url: The URL to scrape
            render_js: Whether to allow JavaScript rendering (default: True)
            wait: Time to wait in milliseconds after page load
            wait_for: CSS selector to wait for (not implemented)
            screenshot: Whether to take a screenshot (not supported)
            extract_rules: Optional extraction rules (not implemented)
            smart_js_detection: Whether to intelligently detect if JS is needed (default: True)
        
        Returns:
            Resource object containing scraped content and metadata
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        # Clean and validate URL
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        start_time = time.time()
        used_js_rendering = False
        
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Step 1: Always try static HTML first (fastest)
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                static_content = response.text
                
                logger.debug(f"Static HTML fetched for {url} ({len(static_content)} chars)")
                
                # Step 2: Intelligent JS detection
                if smart_js_detection and render_js:
                    needs_js = _needs_javascript_rendering(static_content, url)
                    if not needs_js:
                        logger.info(f"Static content sufficient for {url}, skipping JS rendering")
                        content = static_content
                    else:
                        logger.info(f"JS rendering needed for {url}, attempting with Playwright")
                        content = await self._render_with_js(url, wait, static_content)
                        used_js_rendering = True
                elif render_js:
                    # Force JS rendering if requested and smart detection disabled
                    logger.info(f"Force JS rendering for {url}")
                    content = await self._render_with_js(url, wait, static_content)
                    used_js_rendering = True
                else:
                    # Use static content only
                    content = static_content
                    
            except requests.exceptions.RequestException as e:
                # If static request fails, try JS rendering as last resort
                if render_js and (PLAYWRIGHT_AVAILABLE or REQUESTS_HTML_AVAILABLE):
                    logger.warning(f"Static request failed for {url}, trying JS rendering: {e}")
                    content = await self._render_with_js(url, wait)
                    used_js_rendering = True
                else:
                    raise
            
            # Create Resource object
            resource_id = hashlib.md5(url.encode()).hexdigest()
            
            scrape_time = time.time() - start_time
            
            resource_metadata = ResourceMetadata(
                content_type="html",
                length=len(content),
                num_lines=len(content.split('\n')),
                extra={
                    "scraper": "direct_http_optimized",
                    "render_js": used_js_rendering,
                    "wait_time": wait,
                    "scrape_time_seconds": round(scrape_time, 2),
                    "smart_detection": smart_js_detection,
                }
            )
            
            resource = Resource(
                id=resource_id,
                content=content,
                metadata=resource_metadata
            )
            
            logger.info(f"Successfully scraped {url} ({len(content)} chars, {scrape_time:.2f}s, JS: {used_js_rendering})")
            return resource
            
        except Exception as e:
            error_msg = f"Failed to scrape {url}: {str(e)}"
            logger.error(error_msg)
            raise DirectScraperError(error_msg)
    
    async def _render_with_js(self, url: str, wait: int = 1000, fallback_content: str = None) -> str:
        """
        Render page with JavaScript using the best available method
        """
        # Try Playwright first (fastest and most reliable)
        if PLAYWRIGHT_AVAILABLE:
            try:
                return await self._render_with_playwright(url, wait)
            except Exception as e:
                logger.warning(f"Playwright rendering failed for {url}: {e}")
        
        # Fallback to requests-html
        if REQUESTS_HTML_AVAILABLE:
            try:
                response = await self.html_session.get(url, timeout=self.timeout)
                await response.html.arender(timeout=wait/1000)
                return response.html.html
            except Exception as e:
                logger.warning(f"requests-html rendering failed for {url}: {e}")
        
        # If all JS rendering fails, return fallback content or raise error
        if fallback_content:
            logger.warning(f"JS rendering failed for {url}, using static content")
            return fallback_content
        else:
            raise DirectScraperError(f"JavaScript rendering failed and no fallback available for {url}")
    
    async def scrape_multiple_urls(
        self, 
        urls: List[str], 
        render_js: bool = True,
        wait: int = 1000,
        wait_for: Optional[str] = None,
        max_workers: int = 5,
        smart_js_detection: bool = True
    ) -> List[Resource]:
        """
        Scrape content from multiple URLs concurrently for better performance
        
        Args:
            urls: List of URLs to scrape
            render_js: Whether to allow JavaScript rendering (default: True)
            wait: Time to wait in milliseconds after page load (default: 1000ms)
            wait_for: CSS selector to wait for (not implemented)
            max_workers: Maximum number of concurrent workers (default: 5)
            smart_js_detection: Whether to intelligently detect if JS is needed (default: True)
        
        Returns:
            List of Resource objects containing scraped content and metadata
        """
        if not urls:
            raise ValueError("URLs list cannot be empty")
        
        start_time = time.time()
        
        async def scrape_single_url(url: str) -> Resource:
            """Helper function for concurrent scraping"""
            try:
                return await self.scrape_url(
                    url, 
                    render_js=render_js, 
                    wait=wait, 
                    wait_for=wait_for,
                    smart_js_detection=smart_js_detection
                )
            except DirectScraperError as e:
                # Create empty resource for failed scrapes
                logger.warning(f"Failed to scrape {url}: {e}")
                resource_id = hashlib.md5(url.encode()).hexdigest()
                
                return Resource(
                    id=resource_id,
                    content="",
                    metadata=ResourceMetadata(
                        content_type="html",
                        length=0,
                        extra={"scraper": "direct_http_optimized", "error": str(e)}
                    )
                )
            except Exception as e:
                logger.error(f"Unexpected error scraping {url}: {e}")
                # Create empty resource for unexpected errors
                resource_id = hashlib.md5(url.encode()).hexdigest()
                return Resource(
                    id=resource_id,
                    content="",
                    metadata=ResourceMetadata(
                        content_type="html",
                        length=0,
                        extra={"scraper": "direct_http_optimized", "error": str(e)}
                    )
                )
        
        # Use asyncio.gather for concurrent scraping
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_workers)
        
        async def scrape_with_semaphore(url: str) -> Resource:
            async with semaphore:
                return await scrape_single_url(url)
        
        # Execute all scraping tasks concurrently
        results = await asyncio.gather(*[scrape_with_semaphore(url) for url in urls], return_exceptions=False)
        
        # Sort results to maintain original URL order
        url_to_index = {url: i for i, url in enumerate(urls)}
        results.sort(key=lambda r: url_to_index.get(
            next((url for url in urls if hashlib.md5(url.encode()).hexdigest() == r.id), ""), 
            len(urls)
        ))
        
        successful_count = sum(1 for r in results if len(r.content) > 0)
        total_time = time.time() - start_time
        
        logger.info(f"Completed scraping {len(urls)} URLs in {total_time:.2f}s, {successful_count} successful")
        return results


# Convenience functions for easy usage
async def scrape_url(
    url: str, 
    render_js: bool = True, 
    wait: int = 1000,
    wait_for: Optional[str] = None,
    smart_js_detection: bool = True
) -> Resource:
    """
    Convenience function to scrape a single URL using optimized direct scraper
    
    Args:
        url: The URL to scrape
        render_js: Whether to allow JavaScript rendering (default: True)
        wait: Time to wait in milliseconds after page load (default: 1000ms)
        wait_for: CSS selector to wait for (not implemented)
        smart_js_detection: Whether to intelligently detect if JS is needed (default: True)
    
    Returns:
        Resource object containing scraped content and metadata
    """
    scraper = DirectScraper()
    return await scraper.scrape_url(
        url, 
        render_js=render_js, 
        wait=wait, 
        wait_for=wait_for,
        smart_js_detection=smart_js_detection
    )


async def scrape_multiple_urls(
    urls: List[str], 
    render_js: bool = True, 
    wait: int = 1000,
    wait_for: Optional[str] = None,
    max_workers: int = 5,
    smart_js_detection: bool = True
) -> List[Resource]:
    """
    Convenience function to scrape multiple URLs using optimized direct scraper with concurrency
    
    Args:
        urls: List of URLs to scrape
        render_js: Whether to allow JavaScript rendering (default: True)
        wait: Time to wait in milliseconds after page load (default: 1000ms)
        wait_for: CSS selector to wait for (not implemented)
        max_workers: Maximum number of concurrent workers (default: 5)
        smart_js_detection: Whether to intelligently detect if JS is needed (default: True)
    
    Returns:
        List of Resource objects containing scraped content and metadata
    """
    scraper = DirectScraper()
    return await scraper.scrape_multiple_urls(
        urls, 
        render_js=render_js, 
        wait=wait, 
        wait_for=wait_for,
        max_workers=max_workers,
        smart_js_detection=smart_js_detection
    )


# Backward compatibility alias
ScrapingBeeScraper = DirectScraper
