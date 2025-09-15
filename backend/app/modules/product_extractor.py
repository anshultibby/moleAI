"""
Robust Product Extractor using extruct library

This module extracts product data from e-commerce sites by:
1. Using extruct to find JSON-LD, Microdata, and RDFa structured data
2. Following product links and extracting from those pages sequentially
3. Returning normalized product data as SchemaOrgProduct objects
"""

import asyncio
import json
import re
from typing import Dict, List, Set, Tuple, Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger
from extruct import extract
from w3lib.html import get_base_url

from .direct_scraper import DirectScraper
from app.models.product import SchemaOrgProduct


class ProductExtractor:
    """
    Robust product extractor using extruct library for multiple structured data formats.
    
    Usage:
        extractor = ProductExtractor()
        result = await extractor.extract_from_url_and_links(url)
        print(f"Found {len(result)} products")
    """
    
    def __init__(self):
        self.scraper = DirectScraper()
    
    def extract_products_from_html(self, html: str, url: str) -> List[SchemaOrgProduct]:
        """
        Extract products from HTML using extruct library for comprehensive structured data parsing.
        
        Args:
            html: HTML content to search
            url: Base URL for resolving relative URLs
            
        Returns:
            List of SchemaOrgProduct objects
        """
        try:
            base_url = get_base_url(html, url)
            data = extract(html, base_url=base_url, syntaxes=['json-ld', 'microdata', 'rdfa'])
            products = []

            # 1) JSON-LD items
            for block in data.get('json-ld', []):
                items = block if isinstance(block, list) else [block]
                for item in items:
                    # Handle @graph or single objects
                    nodes = item.get('@graph', []) if isinstance(item, dict) else []
                    if nodes:
                        for n in nodes:
                            if self._is_product_like(n): 
                                products.append(n)
                    elif self._is_product_like(item):
                        products.append(item)

            # 2) Microdata and RDFa items
            for md in data.get('microdata', []):
                if self._is_product_like(md.get('type') or md.get('itemtype') or md):
                    products.append(md)
            for r in data.get('rdfa', []):
                if self._is_product_like(r):
                    products.append(r)

            # 3) Normalize and convert to SchemaOrgProduct objects
            normalized = [self._normalize_product(p, base_url) for p in products]
            deduped = self._dedupe_products(normalized)
            
            # Convert to SchemaOrgProduct objects
            schema_products = []
            for product_data in deduped:
                try:
                    # Map the normalized data to SchemaOrgProduct fields
                    schema_product = SchemaOrgProduct(
                        name=product_data.get('name'),
                        brand=product_data.get('brand'),
                        sku=product_data.get('sku'),
                        gtin=product_data.get('gtin'),
                        url=product_data.get('url'),
                        image=product_data.get('image'),
                        description=product_data.get('description'),
                        price=product_data.get('price'),
                        priceCurrency=product_data.get('priceCurrency'),
                        availability=product_data.get('availability'),
                        raw_data=product_data.get('raw', {})
                    )
                    schema_products.append(schema_product)
                except Exception as e:
                    logger.debug(f"Failed to convert to SchemaOrgProduct: {e}")
                    continue
            
            return schema_products
            
        except Exception as e:
            logger.error(f"Failed to extract products from HTML: {e}")
            return []

    def _is_product_like(self, obj: Any) -> bool:
        """Check if an object represents a product-like entity."""
        def get_types(o):
            t = o.get('@type') if isinstance(o, dict) else None
            return [t] if isinstance(t, str) else (t or [])
        
        if not isinstance(obj, dict):
            return False
            
        types_set = {t.lower() for t in get_types(obj)}
        return any(t in types_set for t in ['product', 'offer', 'aggregateoffer'])

    def _normalize_product(self, p: Dict, base_url: str) -> Dict:
        """Normalize product data to a consistent format."""
        def get_value(*keys, default=None):
            """Get value from product data with fallback keys."""
            for k in keys:
                v = p.get(k)
                if v: 
                    return v
            return default
        
        # Handle offers data
        offers = get_value('offers', default={})
        if isinstance(offers, list): 
            offers = offers[0] if offers else {}
        
        # Extract brand name if it's an object
        brand = get_value('brand', default={})
        if isinstance(brand, dict):
            brand = brand.get('name', brand)
        
        return {
            "name": get_value('name', 'title'),
            "brand": brand,
            "sku": get_value('sku'),
            "gtin": get_value('gtin13') or get_value('gtin12') or get_value('gtin14') or get_value('gtin'),
            "url": get_value('url'),
            "image": get_value('image'),
            "description": get_value('description'),
            "price": (offers or {}).get('price'),
            "priceCurrency": (offers or {}).get('priceCurrency'),
            "availability": (offers or {}).get('availability'),
            "raw": p
        }

    def _dedupe_products(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicate products based on SKU, GTIN, name, and price."""
        seen: Set[Tuple] = set()
        out = []
        
        for item in items:
            # Create a key for deduplication
            key = (
                item.get("sku") or item.get("gtin") or item.get("name"), 
                item.get("price")
            )
            if key not in seen:
                seen.add(key)
                out.append(item)
        
        return out
    
    def find_product_links(self, html: str, base_url: str) -> List[str]:
        """
        Find all links that look like product pages.
        
        Args:
            html: HTML content to search
            base_url: Base URL for making relative links absolute
            
        Returns:
            List of product page URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        product_links = []
        
        # Find all links on the page
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
            
            # Make the URL absolute
            full_url = urljoin(base_url, href)
            
            # Check if it looks like a product page
            if self._looks_like_product_url(full_url):
                product_links.append(full_url)
        
        # Remove duplicates
        return list(dict.fromkeys(product_links))
    
    def _looks_like_product_url(self, url: str) -> bool:
        """
        Check if a URL looks like it leads to a product page.
        
        Args:
            url: URL to check
            
        Returns:
            True if it looks like a product URL
        """
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Skip obvious non-product URLs
        skip_words = [
            'cart', 'checkout', 'account', 'login', 'register', 'search',
            'blog', 'about', 'contact', 'help', 'privacy', 'terms',
            '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg'
        ]
        
        for word in skip_words:
            if word in url_lower:
                return False
        
        # Look for product-like patterns
        product_words = ['/product', '/item', '/p/', '/products/']
        
        for word in product_words:
            if word in url_lower:
                return True
        
        return False
    
    async def _scrape_links_for_products(self, urls: List[str]) -> List[SchemaOrgProduct]:
        """
        Scrape multiple URLs sequentially using the shared scraper to avoid connection conflicts.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of SchemaOrgProduct objects from all URLs
        """
        if not urls:
            return []
        
        all_products = []
        
        # Scrape URLs sequentially to avoid Playwright connection conflicts
        logger.info(f"Scraping {len(urls)} URLs sequentially to avoid connection conflicts...")
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Scraping URL {i+1}/{len(urls)}: {url}")
                html = await self.scraper.scrape_url(url, render_js=True, wait=2000, smart_js_detection=True)
                products = self.extract_products_from_html(html, url)
                all_products.extend(products)
                logger.info(f"Found {len(products)} products from {url}")
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")
                continue
        
        logger.info(f"Collected {len(all_products)} total products from {len(urls)} URLs")
        return all_products
    
    async def extract_from_url_and_links(self, url: str, max_links: int = 10) -> List[SchemaOrgProduct]:
        """
        Extract JSON-LD products from a URL and its linked product pages.
        
        This is the main method - it scrapes the given URL, finds product links,
        then scrapes those links in parallel to collect all JSON-LD products.
        
        Args:
            url: The main URL to scrape
            max_links: Maximum number of product links to follow
            
        Returns:
            List of SchemaOrgProduct objects from main page and linked pages
        """
        try:
            logger.info(f"Extracting products from {url} and up to {max_links} linked pages")
            
            # Step 1: Scrape the main page
            html = await self.scraper.scrape_url(url, render_js=True, wait=2000, smart_js_detection=True)
            
            # Step 2: Get products from main page
            main_products = self.find_json_ld_products(html)
            logger.info(f"Found {len(main_products)} products on main page")
            
            # Step 3: Find product links
            product_links = self.find_product_links(html, url)
            if len(product_links) > max_links:
                product_links = product_links[:max_links]
            logger.info(f"Found {len(product_links)} product links to scrape")
            
            # Step 4: Scrape linked pages in parallel
            linked_products = await self._scrape_links_for_products(product_links)
            
            # Step 5: Combine all products
            all_products = main_products + linked_products
            logger.info(f"Total: {len(all_products)} products ({len(main_products)} main + {len(linked_products)} linked)")
            
            return all_products
            
        except Exception as e:
            logger.error(f"Failed to extract products from {url}: {e}")
            return []
        finally:
            await self.scraper.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'scraper'):
            await self.scraper.cleanup()

