"""
Simple Product Extractor

Enhanced heuristic:
1. Get HTML from URL (with JavaScript rendering support for SPAs)
2. Find all product links by filtering URLs with /product/ or /products/
3. Extract JSON-LD from each product page

Clean, focused, and effective - now with SPA support!
"""

import json
import re
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger

# Common user agent to avoid basic bot detection
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def get_html_with_js(url: str, timeout: int = 45, use_stealth: bool = True) -> Optional[str]:
    """
    Get HTML from URL with JavaScript rendering using Playwright.
    
    Enhanced bot detection evasion for sites using PerimeterX, Cloudflare, etc:
    - playwright-stealth library for automatic evasion
    - Advanced stealth mode with full browser fingerprint masking
    - Realistic browser behavior simulation  
    - Human-like interactions (scrolling, delays)
    
    Args:
        url: URL to render
        timeout: Timeout in seconds (default: 45)
        use_stealth: Enable advanced stealth techniques (default: True)
    """
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth
        
        async with async_playwright() as p:
            # Launch with comprehensive bot detection evasion
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-web-security',
                    '--disable-setuid-sandbox',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-sync',
                    '--metrics-recording-only',
                    '--mute-audio',
                    '--no-report-upload',
                    '--lang=en-US',
                ]
            )
            
            # Create context with maximum realism
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=USER_AGENT,
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
            )
            
            # Set additional headers
            await context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            })
            
            page = await context.new_page()
            
            # Apply playwright-stealth for automatic evasion
            if use_stealth:
                stealth_config = Stealth()
                await stealth_config.apply_stealth_async(page)
            
            # Additional manual stealth overrides
            if use_stealth:
                # Comprehensive stealth script to mask automation
                await page.add_init_script("""
                    // Override navigator.webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Overwrite the `plugins` property
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Add chrome object
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // Mock hardware
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => 8
                    });
                    
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: () => 8
                    });
                    
                    // Mock battery
                    Object.defineProperty(navigator, 'getBattery', {
                        value: () => Promise.resolve({
                            charging: true,
                            chargingTime: 0,
                            dischargingTime: Infinity,
                            level: 1.0
                        })
                    });
                    
                    // Override toString to hide proxy
                    const originalToString = Function.prototype.toString;
                    Function.prototype.toString = function() {
                        if (this === Function.prototype.toString) {
                            return 'function toString() { [native code] }';
                        }
                        return originalToString.call(this);
                    };
                    
                    // Mock canvas fingerprint
                    const originalGetContext = HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                        const context = originalGetContext.call(this, type, attributes);
                        if (type === '2d') {
                            const originalGetImageData = context.getImageData;
                            context.getImageData = function() {
                                const imageData = originalGetImageData.apply(this, arguments);
                                for (let i = 0; i < imageData.data.length; i += 4) {
                                    imageData.data[i] = imageData.data[i] ^ 1;
                                }
                                return imageData;
                            };
                        }
                        return context;
                    };
                    
                    // Mock WebGL vendor
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter.call(this, parameter);
                    };
                    
                    // Mock notification permission
                    Object.defineProperty(Notification, 'permission', {
                        get: () => 'default'
                    });
                """)
            
            logger.info(f"Rendering page with JavaScript: {url}")
            
            try:
                # Navigate with domcontentloaded (faster)
                await page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
                
                # Wait a bit for JS to initialize (mimics human reading time)
                await asyncio.sleep(2)
                
                # Simulate human-like scrolling to trigger lazy loading
                if use_stealth:
                    logger.debug("Simulating human scrolling...")
                    await page.evaluate('window.scrollTo(0, 300)')
                    await asyncio.sleep(0.5)
                    await page.evaluate('window.scrollTo(0, 700)')
                    await asyncio.sleep(0.5)
                    await page.evaluate('window.scrollTo(0, 1200)')
                    await asyncio.sleep(0.5)
                    await page.evaluate('window.scrollTo(0, 0)')
                    await asyncio.sleep(1)
                
                # Try to wait for network idle, but don't fail if it times out
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    logger.debug("Network idle timeout, continuing...")
                
                # Try to close any popups/modals
                try:
                    await page.keyboard.press('Escape')
                    await asyncio.sleep(0.5)
                except:
                    pass
                    
            except Exception as e:
                logger.debug(f"Navigation error: {e}")
            
            html = await page.content()
            await browser.close()
            
            logger.info(f"Rendered HTML length: {len(html)} characters")
            
            # Check for bot detection indicators
            html_lower = html.lower()
            if 'captcha' in html_lower or 'perimeterx' in html_lower:
                logger.warning("🚫 Bot detection (PerimeterX/Cloudflare) - skipping this site")
                return None
            
            # Check if response is suspiciously small
            if len(html) < 15000:
                logger.warning(f"Response suspiciously small ({len(html)} chars), possible bot detection")
            
            return html
            
    except ImportError:
        logger.warning("Playwright not available, falling back to simple requests")
        return None
    except Exception as e:
        logger.warning(f"JavaScript rendering failed: {e}, falling back to simple requests")
        return None


def get_html(url: str, timeout: int = 20) -> Optional[str]:
    """Get HTML from URL with realistic headers to avoid bot detection"""
    try:
        import requests
        
        # More realistic headers to avoid bot detection
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/',
        }
        
        response = requests.get(
            url, 
            headers=headers,
            timeout=timeout,
            allow_redirects=True
        )
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def find_product_links(html: str, base_url: str) -> List[str]:
    """
    Find all product links by scanning ALL links and filtering by URL pattern.
    
    Strategy: Instead of looking for 'product' containers (which may not exist),
    find ALL links and keep those with /product/ or /products/ in the URL.
    This is more reliable for modern SPAs and various e-commerce platforms.
    """
    soup = BeautifulSoup(html, 'html.parser')
    product_links = []
    seen_urls = set()
    
    # Find ALL links on the page
    all_links = soup.find_all('a', href=True)
    logger.info(f"Found {len(all_links)} total links on page")
    
    for link in all_links:
        href = link['href']
        
        # Skip empty hrefs, anchors, and javascript links
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        
        # Convert to absolute URL
        full_url = urljoin(base_url, href)
        
        # Parse URL to check if it's from the same domain
        try:
            base_domain = urlparse(base_url).netloc
            link_domain = urlparse(full_url).netloc
            
            # Only keep links from the same domain
            if link_domain != base_domain:
                continue
        except:
            continue
        
        # Filter: only keep product pages
        # Common patterns: /products/, /product/, /p/, /pro/, /pd/, /dp/, /s/
        lower_url = full_url.lower()
        is_product_url = any(pattern in lower_url for pattern in [
            '/products/',
            '/product/',
            '/p/',
            '/pro/',      # Express.com uses /pro/
            '/pd/',       # Some sites use /pd/
            '/dp/',       # Amazon-style /dp/
            '/item/',     # Some sites use /item/
            '/s/',        # Nordstrom uses /s/
        ])
        
        # Exclude collection/category pages
        is_collection_url = any(pattern in lower_url for pattern in [
            '/collections/',
            '/collection/',
            '/category/',
            '/categories/',
        ])
        
        # Only keep if it's a product URL but NOT just a collection URL
        # (some URLs have both, like /collections/xyz/products/abc - those are OK)
        if not is_product_url:
            continue
            
        # Remove duplicates and fragments
        clean_url = full_url.split('#')[0].split('?')[0]  # Remove query params too
        
        # Deduplicate
        if clean_url not in seen_urls and clean_url != base_url:
            seen_urls.add(clean_url)
            product_links.append(clean_url)
    
    logger.info(f"Found {len(product_links)} unique product links")
    return product_links


# ============================================================================
# EXTRACTION STRATEGIES
# ============================================================================

def extract_products_from_listing_json_ld(html: str, url: str) -> List[Dict[str, Any]]:
    """
    NEW STRATEGY: Extract multiple products directly from listing page JSON-LD.
    
    Many e-commerce sites include all products in the listing page as ItemList or CollectionPage
    with embedded Product objects. This is MUCH faster than fetching each product individually.
    
    Returns list of products if found, empty list otherwise.
    """
    try:
        from app.models.product import Product
        
        soup = BeautifulSoup(html, 'html.parser')
        json_ld_data = []
        
        # Find all JSON-LD script tags
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                if script.string:
                    data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        json_ld_data.extend(data)
                    else:
                        json_ld_data.append(data)
            except json.JSONDecodeError:
                continue
        
        products = []
        
        # Look for ItemList or CollectionPage with embedded products
        for item in json_ld_data:
            item_type = item.get('@type', '')
            
            # Handle ItemList
            if item_type == 'ItemList' or item_type == 'CollectionPage':
                items = item.get('itemListElement', []) or item.get('mainEntity', {}).get('itemListElement', [])
                
                for list_item in items:
                    # Sometimes products are nested in 'item' key
                    product_data = list_item.get('item') if 'item' in list_item else list_item
                    
                    if product_data and product_data.get('@type') == 'Product':
                        try:
                            product = Product.from_json_ld(product_data, url)
                            products.append(product.to_dict())
                        except Exception as e:
                            logger.debug(f"Failed to parse embedded product: {e}")
                            continue
            
            # Also check @graph for products
            if '@graph' in item:
                for graph_item in item['@graph']:
                    if graph_item.get('@type') == 'Product':
                        try:
                            product = Product.from_json_ld(graph_item, url)
                            products.append(product.to_dict())
                        except Exception as e:
                            logger.debug(f"Failed to parse graph product: {e}")
                            continue
        
        if products:
            logger.info(f"✓ Extracted {len(products)} products directly from listing page JSON-LD!")
        
        return products
        
    except Exception as e:
        logger.debug(f"Listing page JSON-LD extraction failed: {e}")
        return []


def extract_product_json_ld_strategy(html: str, url: str) -> Optional[Dict[str, Any]]:
    """
    Strategy 1: Extract product using JSON-LD structured data.
    
    Returns raw JSON-LD data to be normalized by Product.from_json_ld()
    """
    try:
        from app.models.product import Product
        
        soup = BeautifulSoup(html, 'html.parser')
        json_ld_data = []
        
        # Find all JSON-LD script tags
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                if script.string:
                    data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        json_ld_data.extend(data)
                    else:
                        json_ld_data.append(data)
            except json.JSONDecodeError:
                continue
        
        # Look for Product type
        for item in json_ld_data:
            if item.get('@type') == 'Product':
                product = Product.from_json_ld(item, url)
                logger.info(f"✓ JSON-LD: {product.product_name}")
                return product.to_dict()
            
            # Sometimes it's nested in @graph
            if '@graph' in item:
                for graph_item in item['@graph']:
                    if graph_item.get('@type') == 'Product':
                        product = Product.from_json_ld(graph_item, url)
                        logger.info(f"✓ JSON-LD: {product.product_name}")
                        return product.to_dict()
        
        return None
    except Exception as e:
        logger.debug(f"JSON-LD strategy failed: {e}")
        return None


def extract_product_nextjs_strategy(html: str, url: str) -> Optional[Dict[str, Any]]:
    """
    Strategy 2: Extract product from Next.js __NEXT_DATA__ object.
    
    Returns raw Next.js data to be normalized by Product.from_nextjs_data()
    """
    try:
        from app.models.product import Product
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the __NEXT_DATA__ script tag
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        if not next_data_script or not next_data_script.string:
            return None
        
        data = json.loads(next_data_script.string)
        
        # Navigate to product data (structure varies by site)
        product_data = None
        
        # Try common paths
        if 'props' in data and 'pageProps' in data['props']:
            page_props = data['props']['pageProps']
            
            # Direct product key
            if 'product' in page_props:
                product_data = page_props['product']
            # Initial props
            elif 'initialProps' in page_props and 'product' in page_props['initialProps']:
                product_data = page_props['initialProps']['product']
        
        if not product_data:
            return None
        
        product = Product.from_nextjs_data(product_data, url)
        logger.info(f"✓ Next.js: {product.product_name}")
        return product.to_dict()
        
    except Exception as e:
        logger.debug(f"Next.js strategy failed: {e}")
        return None


def extract_product_meta_tags_strategy(html: str, url: str) -> Optional[Dict[str, Any]]:
    """
    Strategy 3: Extract product from Open Graph and meta tags.
    
    Returns product data normalized by Product.from_meta_tags()
    """
    try:
        from app.models.product import Product
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = ""
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content', '')
        elif soup.title:
            title = soup.title.string or ''
        
        # Extract description
        description = ""
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            description = og_desc.get('content', '')
        else:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
        
        # Extract image
        image_url = ""
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content', '')
        
        # Extract price from meta tags (if available)
        price = None
        price_meta = soup.find('meta', property='product:price:amount')
        if price_meta:
            try:
                price = float(price_meta.get('content', 0))
            except (ValueError, TypeError):
                pass
        
        currency = "USD"
        currency_meta = soup.find('meta', property='product:price:currency')
        if currency_meta:
            currency = currency_meta.get('content', 'USD')
        
        # Only return if we got at least title and image
        if title and image_url:
            product = Product.from_meta_tags(
                title=title,
                description=description,
                image_url=image_url,
                price=price,
                currency=currency,
                url=url
            )
            logger.info(f"✓ Meta tags: {product.product_name}")
            return product.to_dict()
        
        return None
        
    except Exception as e:
        logger.debug(f"Meta tags strategy failed: {e}")
        return None


async def extract_products_from_links(product_links: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
    """
    Extract products from list of product URLs concurrently.
    
    Tries multiple extraction strategies in order:
    1. JSON-LD structured data (most reliable)
    2. Next.js __NEXT_DATA__ object (for modern SPAs)
    3. Open Graph meta tags (fallback)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_single_product(session: aiohttp.ClientSession, url: str) -> Optional[Dict[str, Any]]:
        async with semaphore:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
                    
                    html = await response.text()
                    
                    # Try extraction strategies in order
                    strategies = [
                        ('JSON-LD', extract_product_json_ld_strategy),
                        ('Next.js Data', extract_product_nextjs_strategy),
                        ('Meta Tags', extract_product_meta_tags_strategy),
                    ]
                    
                    for strategy_name, strategy_func in strategies:
                        product = strategy_func(html, url)
                        if product:
                            # Ensure product_url is set
                            if not product.get('product_url'):
                                product['product_url'] = url
                            return product
                    
                    logger.warning(f"No extraction strategy worked for {url}")
                    return None
                        
            except Exception as e:
                logger.error(f"Failed to extract from {url}: {e}")
                return None
    
    # Extract products concurrently
    async with aiohttp.ClientSession(
        headers={'User-Agent': USER_AGENT},
        timeout=aiohttp.ClientTimeout(total=30)
    ) as session:
        tasks = [extract_single_product(session, url) for url in product_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None results and exceptions
    products = []
    for result in results:
        if isinstance(result, dict) and result:
            products.append(result)
    
    return products


async def extract_products_simple(
    url: str,
    max_products: int = 20,
    context_vars=None
) -> Dict[str, Any]:
    """
    Extract products from an e-commerce listing page.
    
    Uses multiple strategies to handle different site architectures:
    1. Render JavaScript (for SPAs like Hello Molly)
    2. Find product links via URL pattern matching
    3. Extract product data using:
       - JSON-LD structured data (most reliable)
       - Next.js __NEXT_DATA__ object (React/Next.js sites)
       - Open Graph meta tags (fallback)
    
    Args:
        url: E-commerce listing/collection page URL
        max_products: Maximum number of products to extract (default: 50)
        context_vars: Optional context variables (stream_callback, resources, etc.)
    
    Returns:
        Dict with:
        - success: bool
        - products: List[Dict] of extracted products
        - meta: Dict with extraction statistics
        - error: str (if failed)
    """
    
    try:
        logger.info(f"Starting enhanced extraction for: {url}")
        
        # Step 1: Try to get HTML with JavaScript rendering first
        html = await get_html_with_js(url)
        used_js_rendering = True
        
        # Fall back to simple requests if JS rendering failed
        if not html:
            logger.info("Falling back to simple HTTP request")
            html = get_html(url)
            used_js_rendering = False
        
        if not html:
            return {
                "success": False,
                "error": "Failed to fetch HTML",
                "products": []
            }
        
        # Step 2: Find product links using improved strategy
        product_links = find_product_links(html, url)
        
        # If no links found with JS rendering, try again without it
        if not product_links and used_js_rendering:
            logger.info("No links found with JS rendering, trying simple request...")
            html = get_html(url)
            if html:
                product_links = find_product_links(html, url)
        
        if not product_links:
            return {
                "success": False,
                "error": "No product links found",
                "products": [],
                "meta": {
                    "used_js_rendering": used_js_rendering,
                    "html_length": len(html) if html else 0
                }
            }
        
        # Limit number of products to extract
        if len(product_links) > max_products:
            product_links = product_links[:max_products]
            logger.info(f"Limited to first {max_products} product links")
        
        # Step 3: Extract JSON-LD from each product page
        products = await extract_products_from_links(product_links)
        
        logger.info(f"Successfully extracted {len(products)} products")
        
        return {
            "success": True,
            "products": products,
            "meta": {
                "strategy": "enhanced_simple_json_ld",
                "used_js_rendering": used_js_rendering,
                "total_links_found": len(product_links),
                "products_extracted": len(products),
                "success_rate": len(products) / len(product_links) if product_links else 0,
                "html_length": len(html) if html else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Enhanced extraction failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


# Convenience function
async def extract_products_from_url_simple(url: str, max_products: int = 20) -> Dict[str, Any]:
    """Simple interface for product extraction"""
    return await extract_products_simple(url, max_products)
