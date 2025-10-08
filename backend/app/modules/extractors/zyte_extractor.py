"""
Zyte API Product Extractor

Uses Zyte API for reliable HTML fetching with automatic:
- JavaScript rendering
- Bot detection bypassing (PerimeterX, Cloudflare, etc.)
- Proxy rotation
- CAPTCHA solving

Then applies the same extraction strategies from simple_extractor.
"""

import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger

# Import extraction strategies from simple_extractor
from .simple_extractor import (
    find_product_links,
    extract_product_json_ld_strategy,
    extract_product_nextjs_strategy,
    extract_product_meta_tags_strategy,
    extract_products_from_links,
    USER_AGENT
)


ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')
ZYTE_API_URL = 'https://api.zyte.com/v1/extract'


async def get_html_with_zyte(
    url: str,
    javascript_rendering: bool = True,
    session: Optional[aiohttp.ClientSession] = None
) -> Optional[str]:
    """
    Fetch HTML using Zyte API with automatic bot detection bypassing.
    
    Args:
        url: URL to fetch
        javascript_rendering: Enable JavaScript rendering (default: True)
        session: Optional aiohttp session for connection pooling
        
    Returns:
        HTML content or None if failed
    """
    if not ZYTE_API_KEY:
        logger.error("ZYTE_API_KEY not set in environment")
        return None
    
    try:
        # Zyte API request payload
        payload = {
            "url": url,
        }
        
        # Enable JavaScript rendering for SPAs (use browserHtml OR httpResponseBody, not both)
        if javascript_rendering:
            payload["browserHtml"] = True
        else:
            payload["httpResponseBody"] = True
            payload["httpResponseHeaders"] = True
        
        auth = aiohttp.BasicAuth(ZYTE_API_KEY, '')
        
        # Use provided session or create new one
        should_close = False
        if not session:
            session = aiohttp.ClientSession()
            should_close = True
        
        try:
            async with session.post(
                ZYTE_API_URL,
                json=payload,
                auth=auth,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Zyte API error {response.status}: {error_text}")
                    return None
                
                result = await response.json()
                
                # Get HTML from response
                # browserHtml is used if JavaScript rendering was enabled
                html = result.get('browserHtml') or result.get('httpResponseBody')
                
                if html:
                    logger.info(f"✓ Zyte API fetched {len(html)} chars from {url}")
                    return html
                else:
                    logger.error("No HTML in Zyte API response")
                    return None
                    
        finally:
            if should_close:
                await session.close()
                
    except asyncio.TimeoutError:
        logger.error(f"Zyte API timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"Zyte API request failed: {e}")
        return None


async def get_products_with_zyte_automatic_extraction(
    url: str,
    session: Optional[aiohttp.ClientSession] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Use Zyte's automatic product extraction (Alternative approach).
    
    This uses Zyte's built-in AI to extract products directly,
    which can be faster but less customizable than manual extraction.
    
    Args:
        url: Collection/listing page URL
        session: Optional aiohttp session
        
    Returns:
        List of extracted products or None if failed
    """
    if not ZYTE_API_KEY:
        logger.error("ZYTE_API_KEY not set in environment")
        return None
    
    try:
        # Request automatic product list extraction
        payload = {
            "url": url,
            "productList": True,
            "productListOptions": {
                "extractFrom": "httpResponseBody"
            }
        }
        
        auth = aiohttp.BasicAuth(ZYTE_API_KEY, '')
        
        should_close = False
        if not session:
            session = aiohttp.ClientSession()
            should_close = True
        
        try:
            async with session.post(
                ZYTE_API_URL,
                json=payload,
                auth=auth,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Zyte API error {response.status}: {error_text}")
                    return None
                
                result = await response.json()
                product_list = result.get('productList', {}).get('products', [])
                
                if product_list:
                    logger.info(f"✓ Zyte extracted {len(product_list)} products automatically")
                    # Normalize to our product format
                    return [normalize_zyte_product(p) for p in product_list]
                else:
                    logger.warning("No products found by Zyte automatic extraction")
                    return None
                    
        finally:
            if should_close:
                await session.close()
                
    except Exception as e:
        logger.error(f"Zyte automatic extraction failed: {e}")
        return None


def normalize_zyte_product(zyte_product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Zyte's automatic product extraction format to our Product model.
    
    Zyte product format:
    {
        "name": "Product Name",
        "price": "99.99",
        "currency": "USD",
        "url": "https://...",
        "images": [{"url": "https://..."}],
        "description": "...",
        ...
    }
    """
    from app.models.product import Product
    
    try:
        # Extract price
        price = None
        if zyte_product.get('price'):
            try:
                price = float(str(zyte_product['price']).replace(',', ''))
            except (ValueError, TypeError):
                pass
        
        # Extract main image
        image_url = None
        if zyte_product.get('images') and len(zyte_product['images']) > 0:
            image_url = zyte_product['images'][0].get('url')
        
        # Create product using meta tags method (most flexible)
        product = Product.from_meta_tags(
            title=zyte_product.get('name', ''),
            description=zyte_product.get('description', ''),
            image_url=image_url or '',
            price=price,
            currency=zyte_product.get('currency', 'USD'),
            url=zyte_product.get('url', '')
        )
        
        return product.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to normalize Zyte product: {e}")
        return {}


async def extract_products_zyte(
    url: str,
    max_products: int = 50,
    use_automatic_extraction: bool = False,
    context_vars=None
) -> Dict[str, Any]:
    """
    Extract products using Zyte API.
    
    Two modes:
    1. Manual extraction (default): Use Zyte for HTML fetching, then apply our extraction strategies
    2. Automatic extraction: Use Zyte's built-in product extraction AI
    
    Args:
        url: E-commerce listing/collection page URL
        max_products: Maximum number of products to extract
        use_automatic_extraction: Use Zyte's automatic product extraction (faster but less accurate)
        context_vars: Optional context variables
        
    Returns:
        Dict with:
        - success: bool
        - products: List[Dict] of extracted products
        - meta: Dict with extraction statistics
        - error: str (if failed)
    """
    
    if not ZYTE_API_KEY:
        return {
            "success": False,
            "error": "ZYTE_API_KEY not configured",
            "products": []
        }
    
    try:
        logger.info(f"Starting Zyte extraction for: {url}")
        
        # Mode 1: Automatic extraction (faster)
        if use_automatic_extraction:
            products_data = await get_products_with_zyte_automatic_extraction(url)
            
            if products_data:
                return {
                    "success": True,
                    "products": products_data,
                    "meta": {
                        "strategy": "zyte_automatic_extraction",
                        "products_extracted": len(products_data)
                    }
                }
            else:
                # Fall back to manual extraction
                logger.info("Automatic extraction failed, falling back to manual")
        
        # Mode 2: Manual extraction (more reliable)
        # Step 1: Get HTML using Zyte API
        html = await get_html_with_zyte(url, javascript_rendering=True)
        
        if not html:
            return {
                "success": False,
                "error": "Failed to fetch HTML via Zyte API",
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
        
        # Step 3: Fetch each product page via Zyte and extract data
        products = await extract_products_via_zyte(product_links)
        
        logger.info(f"Successfully extracted {len(products)} products via Zyte")
        
        return {
            "success": True,
            "products": products,
            "meta": {
                "strategy": "zyte_manual_extraction",
                "total_links_found": len(product_links),
                "products_extracted": len(products),
                "success_rate": len(products) / len(product_links) if product_links else 0,
                "html_length": len(html)
            }
        }
        
    except Exception as e:
        logger.error(f"Zyte extraction failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


async def extract_products_via_zyte(
    product_links: List[str],
    max_concurrent: int = 3
) -> List[Dict[str, Any]]:
    """
    Extract products from URLs using Zyte API for fetching.
    
    Uses lower concurrency than simple_extractor since Zyte handles the heavy lifting.
    
    Args:
        product_links: List of product URLs
        max_concurrent: Max concurrent requests (default: 3, lower than simple_extractor)
        
    Returns:
        List of extracted products
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_single_product(session: aiohttp.ClientSession, url: str) -> Optional[Dict[str, Any]]:
        async with semaphore:
            try:
                # Fetch HTML via Zyte
                html = await get_html_with_zyte(url, javascript_rendering=True, session=session)
                
                if not html:
                    logger.warning(f"Failed to fetch {url} via Zyte")
                    return None
                
                # Try extraction strategies in order (same as simple_extractor)
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
async def extract_products_from_url_zyte(
    url: str,
    max_products: int = 50,
    use_automatic: bool = False
) -> Dict[str, Any]:
    """
    Simple interface for Zyte-based product extraction.
    
    Args:
        url: Collection/listing page URL
        max_products: Max products to extract
        use_automatic: Use Zyte's automatic extraction (faster but may be less accurate)
    """
    return await extract_products_zyte(url, max_products, use_automatic)
