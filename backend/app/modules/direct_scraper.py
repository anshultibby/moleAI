"""Direct HTTP scraper module with intelligent JavaScript support"""

import os
import re
import asyncio
import requests
import random
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Resource import removed - scraper now returns raw content

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
        self.max_retries = 3
        self.retry_delay_base = 1.0  # Base delay for exponential backoff
        self.session = requests.Session()
        
        # Set up common headers to mimic a real browser with rotation
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        
        # Initialize HTML session for JavaScript rendering if available (fallback)
        # Note: requests-html has threading issues, so we'll create it on-demand
        self.html_session = None
        
        # Playwright browser instance (lazy initialization)
        self._playwright = None
        self._browser = None
        self._browser_lock = asyncio.Lock()
        
        # Base directory for storing raw scraped data
        self.base_data_dir = "/Users/anshul/code/moleAI/backend/resources/chat_history"
    
    def _save_raw_scraped_data(self, resource_name: str, url: str, content: str, metadata: Dict[str, Any], conversation_id: Optional[str] = None) -> str:
        """
        Save raw scraped data to a JSON file in a conversation-specific folder
        
        Args:
            resource_name: The name that would be used for the resource
            url: The URL that was scraped
            content: The raw HTML content
            metadata: Additional metadata about the scrape
            conversation_id: Optional conversation ID to organize files by conversation
            
        Returns:
            The path to the saved JSON file
        """
        try:
            # Determine the directory structure
            if conversation_id:
                # Create conversation-specific folder
                conversation_dir = os.path.join(self.base_data_dir, conversation_id)
                os.makedirs(conversation_dir, exist_ok=True)
                target_dir = conversation_dir
            else:
                # Fallback to base directory
                os.makedirs(self.base_data_dir, exist_ok=True)
                target_dir = self.base_data_dir
            
            # Create filename using resource name and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_{resource_name}_{timestamp}.json"
            filepath = os.path.join(target_dir, filename)
            
            # Prepare data to save
            scraped_data = {
                "resource_name": resource_name,
                "url": url,
                "scraped_at": datetime.now().isoformat(),
                "content_length": len(content),
                "raw_content": content,
                "metadata": metadata,
                "conversation_id": conversation_id
            }
            
            # Save to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(scraped_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved raw scraped data to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save raw scraped data for {resource_name}: {e}")
            return ""
    
    async def _get_browser(self):
        """Lazy initialization of Playwright browser with proper locking"""
        if not PLAYWRIGHT_AVAILABLE:
            return None
            
        async with self._browser_lock:
            browser_needs_restart = False
            if self._browser is None:
                browser_needs_restart = True
            else:
                try:
                    # Check if browser is still connected
                    await self._browser.version()
                except:
                    browser_needs_restart = True
            
            if browser_needs_restart:
                # Clean up old browser if it exists
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
                
                # Create new browser instance
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
                        '--disable-blink-features=AutomationControlled',
                        '--disable-extensions',
                    ]
                )
        return self._browser
    
    async def _render_with_playwright(self, url: str, wait: int = 1000) -> str:
        """Render page with Playwright with improved error handling"""
        browser = await self._get_browser()
        if not browser:
            raise Exception("Playwright not available")
        
        # Create a fresh context for each request to avoid context issues
        context = await browser.new_context(
            user_agent=self.session.headers['User-Agent'],
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True,
            java_script_enabled=True,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        page = None
        try:
            page = await context.new_page()
            
            # Block unnecessary resources for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf,eot}", lambda route: route.abort())
            
            # Navigate to page with better error handling
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
            except Exception as e:
                # Try with networkidle if domcontentloaded fails
                logger.debug(f"domcontentloaded failed for {url}, trying networkidle: {e}")
                await page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
            
            # Smart waiting - wait for network idle or specific time, whichever is shorter
            try:
                await page.wait_for_load_state('networkidle', timeout=min(wait, 3000))
            except:
                # If network idle times out, just wait the specified time
                await page.wait_for_timeout(min(wait, 1000))
            
            content = await page.content()
            return content
            
        finally:
            # Always clean up resources
            if page:
                try:
                    await page.close()
                except:
                    pass
            try:
                await context.close()
            except:
                pass
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Check if function is async or sync
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    # Run sync function in executor
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
            except Exception as e:
                last_exception = e
                
                # Don't retry on certain errors
                if isinstance(e, requests.exceptions.RequestException):
                    if hasattr(e, 'response') and e.response is not None:
                        status_code = e.response.status_code
                        # Don't retry on client errors (except 429 rate limit)
                        if 400 <= status_code < 500 and status_code != 429:
                            if status_code == 403:
                                logger.warning(f"403 Forbidden error, will retry with different approach: {e}")
                            else:
                                logger.error(f"Client error {status_code}, not retrying: {e}")
                                break
                
                if attempt < self.max_retries:
                    delay = self.retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    
                    # Rotate user agent for next attempt
                    self.session.headers['User-Agent'] = random.choice(self.user_agents)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed: {e}")
        
        raise last_exception
    
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
        
        # Close requests session
        if hasattr(self, 'session'):
            self.session.close()
    
    async def scrape_url(
        self, 
        url: str, 
        render_js: bool = True,
        wait: int = 1000,
        wait_for: Optional[str] = None,
        screenshot: bool = False,
        extract_rules: Optional[Dict] = None,
        smart_js_detection: bool = True,
        resource_name: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> str:
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
            resource_name: Optional name for the resource (used for JSON file naming)
            conversation_id: Optional conversation ID to organize files by conversation
        
        Returns:
            String containing scraped HTML content
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
            
            # Step 1: Always try static HTML first (fastest) with retry logic
            def _fetch_static_content():
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            
            try:
                # Run sync function in executor to make it awaitable
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=1) as executor:
                    static_content = await loop.run_in_executor(executor, _fetch_static_content)
                logger.debug(f"Static HTML fetched for {url} ({len(static_content)} chars)")
                
                # Step 2: Intelligent JS detection
                if smart_js_detection and render_js:
                    needs_js = _needs_javascript_rendering(static_content, url)
                    if not needs_js:
                        logger.info(f"Static content sufficient for {url}, skipping JS rendering")
                        content = static_content
                    else:
                        logger.info(f"JS rendering needed for {url}, attempting with Playwright")
                        content = await self._retry_with_backoff(self._render_with_js, url, wait, static_content)
                        used_js_rendering = True
                elif render_js:
                    # Force JS rendering if requested and smart detection disabled
                    logger.info(f"Force JS rendering for {url}")
                    content = await self._retry_with_backoff(self._render_with_js, url, wait, static_content)
                    used_js_rendering = True
                else:
                    # Use static content only
                    content = static_content
                    
            except requests.exceptions.RequestException as e:
                # If static request fails, try JS rendering as last resort
                if render_js and (PLAYWRIGHT_AVAILABLE or REQUESTS_HTML_AVAILABLE):
                    logger.warning(f"Static request failed for {url}, trying JS rendering: {e}")
                    content = await self._retry_with_backoff(self._render_with_js, url, wait)
                    used_js_rendering = True
                else:
                    raise
            
            scrape_time = time.time() - start_time
            
            # Log scraping metadata for debugging
            metadata = {
                "scraper": "direct_http_optimized",
                "render_js": used_js_rendering,
                "wait_time": wait,
                "scrape_time_seconds": round(scrape_time, 2),
                "smart_detection": smart_js_detection,
                "content_length": len(content),
                "num_lines": len(content.split('\n'))
            }
            
            logger.info(f"Successfully scraped {url} ({len(content)} chars, {scrape_time:.2f}s, JS: {used_js_rendering})")
            
            # Save raw scraped data if conversation_id is provided
            if conversation_id and resource_name:
                try:
                    saved_path = self._save_raw_scraped_data(
                        resource_name=resource_name,
                        url=url,
                        content=content,
                        metadata=metadata,
                        conversation_id=conversation_id
                    )
                    logger.debug(f"Saved scraped data to: {saved_path}")
                except Exception as e:
                    logger.warning(f"Failed to save scraped data: {e}")
            
            return content
            
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
        
        # Fallback to requests-html (with threading fix)
        if REQUESTS_HTML_AVAILABLE:
            try:
                # Create session on-demand to avoid threading issues
                if self.html_session is None:
                    self.html_session = AsyncHTMLSession()
                    self.html_session.headers.update(self.session.headers)
                
                # Run in executor to avoid threading issues
                loop = asyncio.get_event_loop()
                
                def _sync_render():
                    import requests_html
                    # Create a new session for this thread
                    session = requests_html.HTMLSession()
                    session.headers.update(self.session.headers)
                    response = session.get(url, timeout=self.timeout)
                    response.html.render(timeout=wait/1000, wait=0.5)
                    return response.html.html
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = loop.run_in_executor(executor, _sync_render)
                    return await future
                    
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
    ) -> List[str]:
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
            List of content strings (empty string for failed scrapes)
        """
        if not urls:
            raise ValueError("URLs list cannot be empty")
        
        start_time = time.time()
        
        async def scrape_single_url(url: str) -> str:
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
                # Return empty string for failed scrapes
                logger.warning(f"Failed to scrape {url}: {e}")
                return ""
            except Exception as e:
                logger.error(f"Unexpected error scraping {url}: {e}")
                # Return empty string for unexpected errors
                return ""
        
        # Use asyncio.gather for concurrent scraping
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_workers)
        
        async def scrape_with_semaphore(url: str) -> str:
            async with semaphore:
                return await scrape_single_url(url)
        
        # Execute all scraping tasks concurrently
        results = await asyncio.gather(*[scrape_with_semaphore(url) for url in urls], return_exceptions=False)
        
        # Results are already in the correct order since we used asyncio.gather
        
        successful_count = sum(1 for content in results if len(content) > 0)
        total_time = time.time() - start_time
        
        logger.info(f"Completed scraping {len(urls)} URLs in {total_time:.2f}s, {successful_count} successful")
        return results


# Convenience functions for easy usage
async def scrape_url(
    url: str, 
    render_js: bool = True, 
    wait: int = 1000,
    wait_for: Optional[str] = None,
    smart_js_detection: bool = True,
    resource_name: Optional[str] = None,
    conversation_id: Optional[str] = None
) -> str:
    """
    Convenience function to scrape a single URL using optimized direct scraper
    
    Args:
        url: The URL to scrape
        render_js: Whether to allow JavaScript rendering (default: True)
        wait: Time to wait in milliseconds after page load (default: 1000ms)
        wait_for: CSS selector to wait for (not implemented)
        smart_js_detection: Whether to intelligently detect if JS is needed (default: True)
        resource_name: Optional name for the resource (used for JSON file naming)
        conversation_id: Optional conversation ID to organize files by conversation
    
    Returns:
        String containing scraped HTML content
    """
    scraper = DirectScraper()
    return await scraper.scrape_url(
        url, 
        render_js=render_js, 
        wait=wait, 
        wait_for=wait_for,
        smart_js_detection=smart_js_detection,
        resource_name=resource_name,
        conversation_id=conversation_id
    )


async def scrape_multiple_urls(
    urls: List[str], 
    render_js: bool = True, 
    wait: int = 1000,
    wait_for: Optional[str] = None,
    max_workers: int = 5,
    smart_js_detection: bool = True
) -> List[str]:
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
        List of content strings (empty string for failed scrapes)
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
