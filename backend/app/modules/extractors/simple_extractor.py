"""
Simple Product Extractor

Simple heuristic:
1. Get HTML from URL
2. Find all href links in divs containing the word "product"
3. Extract JSON-LD from each product page

Clean, focused, and effective.
"""

import json
import re
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger

from app.tools import tool


# Common user agent to avoid basic bot detection
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_html(url: str, timeout: int = 20) -> Optional[str]:
    """Get HTML from URL with basic error handling"""
    try:
        import requests
        response = requests.get(
            url, 
            headers={'User-Agent': USER_AGENT},
            timeout=timeout,
            allow_redirects=True
        )
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def find_product_links(html: str, base_url: str) -> List[str]:
    """Find all href links in divs containing the word 'product'"""
    soup = BeautifulSoup(html, 'html.parser')
    product_links = []
    
    # Find all divs that contain the word 'product' anywhere in their text or attributes
    product_divs = []
    
    # Look for divs with 'product' in class names, data attributes, or text
    for div in soup.find_all('div'):
        div_text = div.get_text().lower()
        div_attrs = ' '.join([str(v) for v in div.attrs.values()]).lower()
        
        if 'product' in div_text or 'product' in div_attrs:
            product_divs.append(div)
    
    # Also look for other common product container elements
    for element in soup.find_all(['article', 'li', 'section']):
        element_text = element.get_text().lower()
        element_attrs = ' '.join([str(v) for v in element.attrs.values()]).lower()
        
        if 'product' in element_text or 'product' in element_attrs:
            product_divs.append(element)
    
    logger.info(f"Found {len(product_divs)} potential product containers")
    
    # Extract all links from these product containers
    for container in product_divs:
        for link in container.find_all('a', href=True):
            href = link['href']
            
            # Skip empty hrefs, anchors, and javascript links
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Convert to absolute URL
            full_url = urljoin(base_url, href)
            
            # Simple filter: only keep product pages (ignore collections for now)
            # Keep URLs with /products/ or /product/
            lower_url = full_url.lower()
            if not any(pattern in lower_url for pattern in ['/products/', '/product/']):
                continue
            
            # Remove duplicates and fragments
            clean_url = full_url.split('#')[0].split('?')[0]  # Remove query params too
            
            if clean_url not in product_links and clean_url != base_url:
                product_links.append(clean_url)
    
    logger.info(f"Found {len(product_links)} unique product links")
    return product_links


def extract_json_ld(html: str) -> List[Dict[str, Any]]:
    """Extract JSON-LD structured data from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    json_ld_data = []
    
    # Find all JSON-LD script tags
    scripts = soup.find_all('script', type='application/ld+json')
    
    for script in scripts:
        try:
            data = json.loads(script.string)
            
            # Handle both single objects and arrays
            if isinstance(data, list):
                json_ld_data.extend(data)
            else:
                json_ld_data.append(data)
                
        except json.JSONDecodeError:
            continue
    
    return json_ld_data


def extract_product_from_json_ld(json_ld_data: List[Dict]) -> Optional[Dict[str, Any]]:
    """Extract product information from JSON-LD data"""
    for item in json_ld_data:
        # Look for Product type
        if item.get('@type') == 'Product':
            return normalize_product(item)
        
        # Sometimes it's nested in @graph
        if '@graph' in item:
            for graph_item in item['@graph']:
                if graph_item.get('@type') == 'Product':
                    return normalize_product(graph_item)
    
    return None


def normalize_product(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize JSON-LD product data to our format"""
    try:
        product = {
            'title': product_data.get('name', ''),
            'description': product_data.get('description', ''),
            'brand': '',
            'price': None,
            'currency': 'USD',
            'image_url': '',
            'sku': product_data.get('sku', ''),
            'product_url': product_data.get('url', ''),
        }
        
        # Extract brand
        brand = product_data.get('brand')
        if isinstance(brand, dict):
            product['brand'] = brand.get('name', '')
        elif isinstance(brand, str):
            product['brand'] = brand
        
        # Extract price from offers
        offers = product_data.get('offers')
        if offers:
            if isinstance(offers, list):
                offer = offers[0] if offers else {}
            else:
                offer = offers
            
            if isinstance(offer, dict):
                price = offer.get('price')
                if price:
                    try:
                        product['price'] = float(price)
                    except (ValueError, TypeError):
                        pass
                
                currency = offer.get('priceCurrency', 'USD')
                product['currency'] = currency
        
        # Extract image
        image = product_data.get('image')
        if image:
            if isinstance(image, list):
                product['image_url'] = image[0] if image else ''
            elif isinstance(image, dict):
                product['image_url'] = image.get('url', '')
            elif isinstance(image, str):
                product['image_url'] = image
        
        return product
        
    except Exception as e:
        logger.error(f"Error normalizing product: {e}")
        return None


async def extract_products_from_links(product_links: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
    """Extract products from list of product URLs concurrently"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_single_product(session: aiohttp.ClientSession, url: str) -> Optional[Dict[str, Any]]:
        async with semaphore:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status == 200:
                        html = await response.text()
                        json_ld_data = extract_json_ld(html)
                        product = extract_product_from_json_ld(json_ld_data)
                        
                        if product:
                            # Ensure product_url is set
                            if not product.get('product_url'):
                                product['product_url'] = url
                            logger.info(f"Extracted product: {product.get('title', 'Unknown')}")
                            return product
                        else:
                            logger.warning(f"No product JSON-LD found in {url}")
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
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


@tool(
    name="extract_products_simple",
    description="""Simple product extraction using a 3-step heuristic:
    
    1. Get HTML from the listing page URL
    2. Find all href links in divs/containers containing the word 'product'
    3. Extract JSON-LD structured data from each product page
    
    This approach is clean, focused, and works well for most e-commerce sites
    that use proper structured data markup.
    """
)
async def extract_products_simple(
    url: str,
    max_products: int = 50,
    context_vars=None
) -> Dict[str, Any]:
    """
    Simple product extraction following the 3-step heuristic:
    1. Get HTML from URL
    2. Find product links
    3. Extract JSON-LD from each
    """
    
    try:
        logger.info(f"Starting simple extraction for: {url}")
        
        # Step 1: Get HTML from listing page
        html = get_html(url)
        if not html:
            return {
                "success": False,
                "error": "Failed to fetch HTML",
                "products": []
            }
        
        # Step 2: Find product links
        product_links = find_product_links(html, url)
        if not product_links:
            return {
                "success": False,
                "error": "No product links found",
                "products": []
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
                "strategy": "simple_json_ld",
                "total_links_found": len(product_links),
                "products_extracted": len(products),
                "success_rate": len(products) / len(product_links) if product_links else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Simple extraction failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


# Convenience function
async def extract_products_from_url_simple(url: str, max_products: int = 50) -> Dict[str, Any]:
    """Simple interface for product extraction"""
    return await extract_products_simple(url, max_products)
