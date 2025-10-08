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
import html as ihtml
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger

# Common user agent to avoid basic bot detection
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _coerce_price_currency(text):
    """Helper to extract price and currency from text"""
    if not text: 
        return None, None
    m = re.search(r'(?P<cur>[$£€])?\s*(?P<amt>\d+(?:[.,]\d{2})?)', str(text))
    if not m: 
        return None, None
    amt = float(m.group('amt').replace(',', ''))
    cur = {'$':'USD','£':'GBP','€':'EUR'}.get(m.group('cur'), None)
    return amt, cur


def is_shopify(html: str) -> bool:
    """Detect if a site is powered by Shopify"""
    if not html:
        return False
    html_lower = html.lower()
    return any([
        'cdn.shopify.com' in html_lower,
        'window.shopify' in html_lower,
        'shopify.theme' in html_lower,
        'shopify-features' in html_lower,
        '/cdn/shop/' in html_lower
    ])


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

def extract_products_from_inline_state(html: str, base_url: str, max_products: int = 40) -> List[Dict[str, Any]]:
    """
    SUPER FAST STRATEGY: Mine pre-hydration JSON blobs from SPAs.
    
    Many modern e-commerce sites embed complete product data in JSON blobs for
    client-side hydration. This is MUCH faster than parsing HTML!
    
    Supports:
    - Next.js (__NEXT_DATA__)
    - Nuxt (__NUXT__)
    - Apollo GraphQL (__APOLLO_STATE__)
    - Redux/generic (__INITIAL_STATE__)
    - Generic <script type="application/json"> tags (Shopify, Remix, etc.)
    
    Returns list of products if found, empty list otherwise.
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        candidates = []

        # 1) Next.js __NEXT_DATA__
        tag = soup.find('script', id='__NEXT_DATA__')
        if tag and tag.string:
            try: 
                candidates.append(json.loads(tag.string))
                logger.debug("Found __NEXT_DATA__ blob")
            except: 
                pass

        # 2) Nuxt __NUXT__
        nuxt_text = None
        for s in soup.find_all('script'):
            txt = s.string or ''
            if '__NUXT__' in txt:
                nuxt_text = txt
                break
        if nuxt_text:
            m = re.search(r'__NUXT__\s*=\s*({.*});?', nuxt_text, flags=re.S)
            if m:
                try: 
                    candidates.append(json.loads(m.group(1)))
                    logger.debug("Found __NUXT__ blob")
                except: 
                    pass

        # 3) Apollo GraphQL __APOLLO_STATE__
        apollo = None
        for s in soup.find_all('script'):
            txt = s.string or ''
            if '__APOLLO_STATE__' in txt:
                apollo = txt
                break
        if apollo:
            m = re.search(r'__APOLLO_STATE__\s*=\s*({.*});?', apollo, flags=re.S)
            if m:
                try: 
                    candidates.append(json.loads(m.group(1)))
                    logger.debug("Found __APOLLO_STATE__ blob")
                except: 
                    pass

        # 4) Additional window state patterns
        for s in soup.find_all('script'):
            txt = s.string or ''
            # Shopify Hydrogen __STOREFRONT_DATA__
            if '__STOREFRONT_DATA__' in txt:
                m = re.search(r'__STOREFRONT_DATA__\s*=\s*({.*?});?', txt, flags=re.S)
                if m:
                    try:
                        candidates.append(json.loads(m.group(1)))
                        logger.debug("Found __STOREFRONT_DATA__ blob")
                    except:
                        pass
            # Redux __INITIAL_STATE__
            if '__INITIAL_STATE__' in txt:
                m = re.search(r'__INITIAL_STATE__\s*=\s*({.*?});?', txt, flags=re.S)
                if m:
                    try:
                        candidates.append(json.loads(m.group(1)))
                        logger.debug("Found __INITIAL_STATE__ blob")
                    except:
                        pass

        # 5) Generic JSON blobs (Shopify, Remix, etc.)
        for s in soup.find_all('script', attrs={'type':'application/json'}):
            if not s.string:
                continue
            try:
                candidates.append(json.loads(s.string))
            except: 
                # Sometimes HTML-escaped; unescape & retry
                try: 
                    candidates.append(json.loads(ihtml.unescape(s.string)))
                except: 
                    pass

        if candidates:
            logger.debug(f"Found {len(candidates)} JSON candidates to mine")

        # Walk candidates and extract product-like objects
        products = []
        
        def push(prod):
            """Extract and normalize a product-like dict"""
            name = prod.get('title') or prod.get('name') or prod.get('productTitle') or ''
            if not name: 
                return
            
            url = prod.get('url') or prod.get('product_url') or prod.get('href') or prod.get('link') or ''
            if url: 
                url = urljoin(base_url, url)
            
            # Extract image
            img = None
            img_field = prod.get('image') or prod.get('images') or prod.get('img')
            if isinstance(img_field, dict):
                img = img_field.get('url') or img_field.get('src')
            elif isinstance(img_field, list) and img_field:
                first = img_field[0]
                img = first.get('url') or first.get('src') if isinstance(first, dict) else first
            elif isinstance(img_field, str):
                img = img_field
            
            # Extract price
            price = None
            currency = None
            for key in ['price','priceValue','currentPrice','minPrice','price_amount','amount','amountMin','variants']:
                if key in prod:
                    val = prod[key]
                    # Handle variants array (common in Shopify)
                    if key == 'variants' and isinstance(val, list) and val:
                        val = val[0].get('price') if isinstance(val[0], dict) else None
                    if isinstance(val, (int, float, str)):
                        price, currency = _coerce_price_currency(str(val))
                        if price is not None: 
                            break
            
            # Try offers (Schema.org format)
            if not price and 'offers' in prod:
                off = prod['offers']
                if isinstance(off, list) and off:
                    off = off[0]
                if isinstance(off, dict):
                    price, _ = _coerce_price_currency(str(off.get('price', '')))
                    currency = off.get('priceCurrency') or currency
            
            # Extract brand
            brand = ''
            brand_field = prod.get('brand') or prod.get('vendor')
            if isinstance(brand_field, dict):
                brand = brand_field.get('name', '')
            elif isinstance(brand_field, str):
                brand = brand_field
            
            products.append({
                "product_name": name,
                "url": url or base_url,
                "price": price,
                "currency": currency or prod.get('currency') or 'USD',
                "image_url": img,
                "description": prod.get('description', ''),
                "brand": brand,
                "sku": prod.get('sku', ''),
                "availability": prod.get('availability') or 'InStock'
            })

        def walk(x, depth=0):
            """Recursively walk nested dicts/lists looking for product-like shapes"""
            if depth > 10:  # Prevent infinite recursion
                return
            
            if isinstance(x, dict):
                keys = set(k.lower() for k in x.keys())
                # Looks like a product if it has name/title AND (price OR image OR offers)
                looks_like_product = (
                    ('title' in keys or 'name' in keys or 'producttitle' in keys) and 
                    ('price' in keys or 'offers' in keys or 'image' in keys or 'images' in keys or 'variants' in keys)
                )
                if looks_like_product:
                    push(x)
                
                # Continue walking
                for v in x.values():
                    walk(v, depth + 1)
                    if len(products) >= max_products:
                        return
            
            elif isinstance(x, list):
                for v in x:
                    walk(v, depth + 1)
                    if len(products) >= max_products:
                        return

        # Walk all candidates
        for cand in candidates:
            walk(cand)
            if len(products) >= max_products:
                break

        # De-dupe by (name, url)
        seen = set()
        uniq = []
        for p in products:
            k = (p['product_name'], p['url'])
            if k in seen:
                continue
            seen.add(k)
            uniq.append(p)
            if len(uniq) >= max_products:
                break

        if uniq:
            logger.info(f"⚡ SUPER FAST: Extracted {len(uniq)} products from inline JSON state!")
        
        return uniq
        
    except Exception as e:
        logger.debug(f"Inline state extraction failed: {e}")
        return []


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
            
            # Handle both string and array @type values
            is_item_list = item_type == 'ItemList' or (isinstance(item_type, list) and 'ItemList' in item_type)
            is_collection_page = item_type == 'CollectionPage' or (isinstance(item_type, list) and 'CollectionPage' in item_type)
            
            # Handle ItemList or CollectionPage
            if is_item_list or is_collection_page:
                items = item.get('itemListElement', []) or item.get('mainEntity', {}).get('itemListElement', [])
                
                for list_item in items:
                    # Sometimes products are nested in 'item' key
                    product_data = list_item.get('item') if 'item' in list_item else list_item
                    
                    # Check if this is a Product (handle both string and array @type)
                    type_value = product_data.get('@type', '')
                    is_product = type_value == 'Product' or (isinstance(type_value, list) and 'Product' in type_value)
                    
                    if product_data and is_product:
                        try:
                            product = Product.from_json_ld(product_data, url)
                            products.append(product.to_dict())
                        except Exception as e:
                            logger.debug(f"Failed to parse embedded product: {e}")
                            continue
            
            # Also check @graph for products
            if '@graph' in item:
                for graph_item in item['@graph']:
                    # Check if this is a Product (handle both string and array @type)
                    type_value = graph_item.get('@type', '')
                    is_product = type_value == 'Product' or (isinstance(type_value, list) and 'Product' in type_value)
                    
                    if is_product:
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


def extract_products_from_html_grid(html: str, base_url: str, max_products: int = 20) -> List[Dict[str, Any]]:
    """
    FASTEST STRATEGY: Extract products directly from HTML product grid/listing.
    
    This scrapes the visible product cards on collection pages - the exact products
    you see when you visit the page in a browser. No need to visit individual pages!
    
    Common patterns:
    - Product cards with class containing: product, item, card, grid-item
    - Title in: h2, h3, a.title, .product-title, .product-name
    - Price in: .price, .money, span with $ or price class
    - Image in: img tags within product card
    - Link in: a tags with href to /products/, /collections/, /p/
    
    Returns list of products extracted from the grid.
    """
    try:
        from app.models.product import Product
        from urllib.parse import urljoin
        import re
        
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # Common product card selectors (ordered by specificity - most specific first!)
        product_card_selectors = [
            '[data-product-id]',  # Most specific - has actual product data
            '[data-product]',
            '.product-grid-item',
            '.product-item',
            '[class*="ProductItem"]',
            'li.product',
            'article.product',
            'div.product',
            '.grid-item',
            '[class*="product-item"]',
            '.product-card',  # Less specific - often just wrappers
            '[class*="product-card"]',
            '[class*="ProductCard"]',
        ]
        
        product_cards = []
        for selector in product_card_selectors:
            product_cards = soup.select(selector)
            if len(product_cards) >= 1:  # Accept any product cards found
                logger.info(f"Found {len(product_cards)} products using selector: {selector}")
                break
        
        if not product_cards:
            logger.debug("No product grid found in HTML")
            return []
        
        skipped_no_link = 0
        skipped_bad_url = 0
        skipped_no_title = 0
        
        for card in product_cards[:max_products]:
            try:
                # Extract product URL - try data attributes first (common in Shopify)
                product_url = None
                link_elem = None
                
                # Strategy 1: Check for data-product-url or similar attributes
                for attr in ['data-product-url', 'data-url', 'data-href', 'data-product-href']:
                    if card.get(attr):
                        product_url = urljoin(base_url, card[attr])
                        # Create a fake link elem for title extraction later
                        link_elem = card
                        break
                
                # Strategy 2: Extract product link (try multiple patterns)
                if not product_url:
                    link_elem = card.find('a', href=True)
                    
                    # If no direct link, look for nested links
                    if not link_elem:
                        # Try finding ANY link within the card
                        link_elem = card.find_all('a', href=True)
                        if link_elem:
                            # Prefer links with product-related classes or that go to /products/
                            for link in link_elem:
                                href = link.get('href', '')
                                if '/product' in href.lower() or 'product' in (link.get('class') or []):
                                    link_elem = link
                                    break
                            # If no product link found, use first link
                            if isinstance(link_elem, list):
                                link_elem = link_elem[0] if link_elem else None
                    
                    if not link_elem or not link_elem.get('href'):
                        skipped_no_link += 1
                        continue
                    
                    product_url = urljoin(base_url, link_elem['href'])
                
                # Skip non-product links (cart, search, etc)
                if any(x in product_url.lower() for x in ['cart', 'search', 'account', 'login', 'wishlist']):
                    skipped_bad_url += 1
                    continue
                
                # Extract title (try multiple patterns)
                title = None
                
                # First try data attributes (common in Shopify)
                for attr in ['data-product-title', 'data-title', 'data-name', 'data-product-name']:
                    if card.get(attr):
                        title = card[attr]
                        break
                
                # Then try selectors
                if not title:
                    for selector in ['.product-title', '.product-name', 'h2', 'h3', 'h4', '.title', '[class*="title"]', '[class*="Title"]', '[class*="name"]']:
                        title_elem = card.select_one(selector)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if title:  # Make sure it's not empty
                                break
                
                if not title and link_elem:
                    # Fallback 1: Try aria-label on the link
                    title = link_elem.get('aria-label', '')
                
                if not title:
                    # Fallback 2: Try img alt text
                    img = card.find('img')
                    if img:
                        title = img.get('alt', '')
                
                if not title and link_elem and hasattr(link_elem, 'get_text'):
                    # Fallback 3: use link text
                    title = link_elem.get_text(strip=True)
                
                # Reject useless titles (common button/link text that isn't the product name)
                useless_titles = ['quick view', 'shop now', 'view', 'buy now', 'add to cart', 'learn more', 'details', 'see more', 'quick add']
                if title and title.lower().strip() in useless_titles:
                    title = None
                
                # Fallback 4: If we have a URL but no title, extract from URL
                if not title and product_url:
                    # Extract product slug from URL (e.g., /products/stormi-dress -> "stormi dress")
                    url_parts = product_url.rstrip('/').split('/')
                    if url_parts:
                        slug = url_parts[-1]
                        # Convert slug to title (replace - and _ with spaces, capitalize)
                        title = slug.replace('-', ' ').replace('_', ' ').title()
                
                if not title:
                    skipped_no_title += 1
                    logger.debug(f"Skipped card (no title): URL={product_url}, has link_elem: {bool(link_elem)}")
                    continue
                
                # Extract price (try multiple patterns)
                price = None
                currency = "USD"
                
                # First try data attributes
                for attr in ['data-price', 'data-product-price']:
                    if card.get(attr):
                        try:
                            price = float(str(card[attr]).replace(',', '').replace('$', '').replace('£', '').replace('€', ''))
                            break
                        except ValueError:
                            pass
                
                # Then try selectors
                if price is None:
                    for selector in ['.price', '.money', '[class*="price"]', '[class*="Price"]']:
                        price_elem = card.select_one(selector)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            # Extract numeric price
                            match = re.search(r'[\$£€]?\s*(\d+(?:[.,]\d{2})?)', price_text)
                            if match:
                                try:
                                    price = float(match.group(1).replace(',', ''))
                                    # Detect currency
                                    if '$' in price_text:
                                        currency = "USD"
                                    elif '£' in price_text:
                                        currency = "GBP"
                                    elif '€' in price_text:
                                        currency = "EUR"
                                    break
                                except ValueError:
                                    pass
                
                # Extract image
                image_url = None
                img_elem = card.find('img')
                if img_elem:
                    # Try different image attributes
                    for attr in ['src', 'data-src', 'data-srcset', 'srcset']:
                        if img_elem.get(attr):
                            img_url = img_elem[attr]
                            # Handle srcset (take first URL)
                            if ' ' in img_url:
                                img_url = img_url.split()[0]
                            image_url = urljoin(base_url, img_url)
                            break
                
                # Create product dict
                if title:  # Minimum requirement
                    product_dict = {
                        "product_name": title,
                        "url": product_url,
                        "price": price,
                        "currency": currency,
                        "image_url": image_url,
                        "description": "",
                        "brand": "",
                        "sku": "",
                        "availability": "InStock"
                    }
                    
                    products.append(product_dict)
                    logger.debug(f"✓ Grid extraction: {title} - ${price}")
                
            except Exception as e:
                logger.debug(f"Failed to parse product card: {e}")
                continue
        
        if products:
            logger.info(f"🎯 FAST PATH: Extracted {len(products)} products directly from HTML grid!")
        else:
            logger.debug(f"Grid scraping failed: skipped {skipped_no_link} (no link), {skipped_bad_url} (bad URL), {skipped_no_title} (no title)")
        
        return products
        
    except Exception as e:
        logger.debug(f"HTML grid extraction failed: {e}")
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
