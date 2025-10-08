"""
BrightData Web Unlocker API Product Extractor

Uses BrightData's Web Unlocker API (simpler than proxy method) with:
- Automatic bot detection bypassing
- JavaScript rendering
- Residential proxy rotation
- CAPTCHA solving

Pricing: $1.50-2.50 per 1000 requests (cheaper than Zyte!)

API Documentation: https://docs.brightdata.com/api-reference/web-unlocker/introduction
"""

import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from loguru import logger

# Import extraction strategies from simple_extractor
from .simple_extractor import (
    find_product_links,
    extract_product_json_ld_strategy,
    extract_product_nextjs_strategy,
    extract_product_meta_tags_strategy,
    USER_AGENT
)


BRIGHTDATA_API_KEY = os.getenv('BRIGHTDATA_API_KEY')
BRIGHTDATA_ZONE = os.getenv('BRIGHTDATA_ZONE', 'web_unlocker1')


async def get_html_with_brightdata_api(
    url: str,
    render_js: bool = True,
    session: Optional[aiohttp.ClientSession] = None
) -> Optional[str]:
    """
    Fetch HTML using BrightData Web Unlocker API.
    
    This is simpler than the proxy method and supports:
    - Automatic bot detection bypass
    - JavaScript rendering
    - Proxy rotation
    - CAPTCHA solving
    
    Args:
        url: URL to fetch
        render_js: Enable JavaScript rendering (default: True)
        session: Optional aiohttp session for connection pooling
        
    Returns:
        HTML content or None if failed
    """
    if not BRIGHTDATA_API_KEY:
        logger.error("BRIGHTDATA_API_KEY not set in environment")
        return None
    
    try:
        # BrightData Web Unlocker API endpoint
        api_url = "https://api.brightdata.com/request"
        
        # URL-encode to handle spaces and special characters
        # Parse URL to only encode the path/query parts, not the scheme/domain
        from urllib.parse import urlsplit, urlunsplit
        parts = urlsplit(url)
        # Only encode the path and query, leave scheme and netloc as-is
        encoded_url = urlunsplit((
            parts.scheme,
            parts.netloc,
            quote(parts.path, safe='/'),
            quote(parts.query, safe='=&'),
            parts.fragment
        ))
        
        # Request payload
        payload = {
            "zone": BRIGHTDATA_ZONE,
            "url": encoded_url,
            "format": "raw"  # Get raw HTML
        }
        
        # Add JavaScript rendering if needed
        if render_js:
            payload["render"] = True
        
        headers = {
            "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Use provided session or create new one
        should_close = False
        if not session:
            session = aiohttp.ClientSession()
            should_close = True
        
        try:
            async with session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"BrightData API error {response.status}: {error_text}")
                    return None
                
                html = await response.text()
                
                if html:
                    logger.info(f"✓ BrightData API fetched {len(html)} chars from {url}")
                    return html
                else:
                    logger.error("Empty response from BrightData API")
                    return None
                    
        finally:
            if should_close:
                await session.close()
                
    except asyncio.TimeoutError:
        logger.error(f"BrightData API timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"BrightData API request failed: {e}")
        return None


async def extract_products_brightdata_api(
    url: str,
    max_products: int = 50,
    context_vars=None
) -> Dict[str, Any]:
    """
    Extract products using BrightData Web Unlocker API.
    
    Process:
    1. Use BrightData API to fetch listing page HTML (with JS rendering)
    2. Find product links using URL pattern matching
    3. Fetch each product page via BrightData API
    4. Extract product data using multiple strategies
    
    Args:
        url: E-commerce listing/collection page URL
        max_products: Maximum number of products to extract
        context_vars: Optional context variables
        
    Returns:
        Dict with:
        - success: bool
        - products: List[Dict] of extracted products
        - meta: Dict with extraction statistics
        - error: str (if failed)
    """
    
    if not BRIGHTDATA_API_KEY:
        return {
            "success": False,
            "error": "BRIGHTDATA_API_KEY not configured",
            "products": []
        }
    
    try:
        logger.info(f"Starting BrightData API extraction for: {url}")
        
        # Step 1: Get HTML using BrightData API
        html = await get_html_with_brightdata_api(url, render_js=True)
        
        if not html:
            return {
                "success": False,
                "error": "Failed to fetch HTML via BrightData API",
                "products": []
            }
        
        # Step 2: Find product links
        product_links = find_product_links(html, url)
        
        if not product_links:
            return {
                "success": False,
                "error": "No product links found",
                "products": [],
                "meta": {
                    "html_length": len(html)
                }
            }
        
        # Limit number of products
        if len(product_links) > max_products:
            product_links = product_links[:max_products]
            logger.info(f"Limited to first {max_products} product links")
        
        # Step 3: Fetch each product page via BrightData API and extract data
        products = await extract_products_via_brightdata_api(product_links)
        
        logger.info(f"Successfully extracted {len(products)} products via BrightData API")
        
        return {
            "success": True,
            "products": products,
            "meta": {
                "strategy": "brightdata_web_unlocker_api",
                "total_links_found": len(product_links),
                "products_extracted": len(products),
                "success_rate": len(products) / len(product_links) if product_links else 0,
                "html_length": len(html)
            }
        }
        
    except Exception as e:
        logger.error(f"BrightData API extraction failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


async def extract_products_via_brightdata_api(
    product_links: List[str],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract products from URLs using BrightData API.
    
    Args:
        product_links: List of product URLs
        max_concurrent: Max concurrent requests (default: 5)
        
    Returns:
        List of extracted products
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_single_product(session: aiohttp.ClientSession, url: str) -> Optional[Dict[str, Any]]:
        async with semaphore:
            try:
                # Fetch HTML via BrightData API
                html = await get_html_with_brightdata_api(url, render_js=True, session=session)
                
                if not html:
                    logger.warning(f"Failed to fetch {url} via BrightData API")
                    return None
                
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
                        logger.debug(f"✓ {strategy_name} extracted: {product.get('product_name', 'Unknown')}")
                        return product
                
                logger.warning(f"No extraction strategy worked for {url}")
                return None
                    
            except Exception as e:
                logger.error(f"Failed to extract from {url}: {e}")
                return None
    
    # Create single session for all requests
    async with aiohttp.ClientSession() as session:
        tasks = [extract_single_product(session, url) for url in product_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None results and exceptions
    products = []
    for result in results:
        if isinstance(result, dict) and result:
            products.append(result)
    
    return products


# Convenience function
async def extract_products_from_url_brightdata_api(
    url: str,
    max_products: int = 50
) -> Dict[str, Any]:
    """
    Simple interface for BrightData API-based product extraction.
    
    Args:
        url: Collection/listing page URL
        max_products: Max products to extract
    """
    return await extract_products_brightdata_api(url, max_products)
