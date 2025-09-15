"""
Intelligent Product Crawler

This module extracts product data from e-commerce sites by:
1. Crawling the website intelligently (prioritizing product pages)
2. Extracting structured data (JSON-LD, Microdata, RDFa)
3. Normalizing products into SchemaOrgProduct objects
"""

import asyncio
import re
from typing import List
from urllib.parse import urljoin, urldefrag, urlparse
from collections import deque

import aiohttp
from bs4 import BeautifulSoup
from extruct import extract as extruct_extract
from w3lib.html import get_base_url
from loguru import logger

from app.models.product import SchemaOrgProduct


class ProductExtractor:
    """
    Intelligent product crawler that extracts structured data from e-commerce sites.
    
    Usage:
        extractor = ProductExtractor()
        result = await extractor.extract_from_url_and_links(url)
        print(f"Found {len(result)} products")
    """
    
    # Configuration
    MAX_DEPTH = 2
    CONCURRENCY = 8
    TIMEOUT = 20
    USER_AGENT = "ProductExtractorBot/1.0 (+mailto:you@example.com)"
    
    # Regex patterns
    ALLOWED_CONTENT_RE = re.compile(r"text/html")
    PRODUCT_HINTS_RE = re.compile(r"/(product|p/|sku|item|dp/)", re.I)
    PAGINATION_HINTS_RE = re.compile(r"(page=\d+|/page/\d+|p=\d+)", re.I)
    
    def __init__(self):
        pass
    
    def _same_host(self, a: str, b: str) -> bool:
        """Check if two URLs are from the same host."""
        return urlparse(a).netloc == urlparse(b).netloc
    
    def _canonicalize(self, url: str) -> str:
        """Canonicalize URL by removing fragments and tracking parameters."""
        url, _ = urldefrag(url)
        parsed = urlparse(url)
        # Drop common tracking params
        drop = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}
        q = "&".join([kv for kv in parsed.query.split("&") if kv and kv.split("=")[0] not in drop])
        return parsed._replace(query=q).geturl()
    
    def _is_candidate_link(self, href: str, root: str) -> bool:
        """Check if a link is worth following."""
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            return False
        url = urljoin(root, href)
        if not self._same_host(url, root):
            return False
        path = urlparse(url).path.lower()
        # Avoid non-page assets
        if any(path.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", 
                                             ".pdf", ".zip", ".mp4", ".css", ".js", ".ico", 
                                             ".woff", ".woff2", ".ttf", ".map")):
            return False
        return True
    
    def _classify_url(self, url: str) -> str:
        """Classify URL type for crawl prioritization."""
        if self.PRODUCT_HINTS_RE.search(url):
            return "product"
        if (self.PAGINATION_HINTS_RE.search(url) or 
            any(x in url.lower() for x in ["/page/", "/category/", "/collection/", "/collections/", "/shop/", "/search", "/s?"])):
            return "listing"
        return "other"
    
    def _extract_product_links_from_listing(self, html: str, base_url: str) -> List[str]:
        """Extract product page links from listing/collection pages."""
        soup = BeautifulSoup(html, "html.parser")
        product_links = []
        
        # Common selectors for product links on e-commerce sites
        selectors = [
            'a[href*="/product"]',
            'a[href*="/p/"]', 
            'a[href*="/item"]',
            'a[href*="/dp/"]',  # Amazon
            '.product-item a',
            '.product-card a',
            '.product-link',
            '[data-product-url]',
            'a.product',
            '.grid-product__link',
            '.product-tile a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href') or link.get('data-product-url')
                if href and self._is_candidate_link(href, base_url):
                    full_url = urljoin(base_url, href)
                    if self._classify_url(full_url) == "product":
                        product_links.append(self._canonicalize(full_url))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in product_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        return unique_links
    
    def _is_product_like(self, obj: dict) -> bool:
        """Check if an object represents a product."""
        def get_types(o):
            t = o.get('@type') if isinstance(o, dict) else None
            return [t] if isinstance(t, str) else (t or [])
        
        types = {t.lower() for t in get_types(obj)}
        return any(t in types for t in ['product', 'offer', 'aggregateoffer'])
    
    def _normalize_product(self, product_data: dict) -> dict:
        """Normalize product data to a consistent format."""
        def get_value(*keys, default=None):
            for k in keys:
                v = product_data.get(k)
                if v:
                    return v
            return default
        
        # Handle offers data properly
        offers = get_value('offers', default={})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        
        # Handle brand data
        brand = get_value('brand', default=None)
        if isinstance(brand, dict):
            brand = brand.get('name') or brand.get('@id') or str(brand)
        
        # Handle description with multiple possible field names
        description = get_value('description', 'desc', 'summary', 'details', 'about', default=None)
        
        # Handle image data (can be string or object)
        image = get_value('image')
        if isinstance(image, dict):
            image = image.get('url') or image.get('@id') or image.get('contentUrl')
        elif isinstance(image, list) and image:
            first_img = image[0]
            if isinstance(first_img, dict):
                image = first_img.get('url') or first_img.get('@id') or first_img.get('contentUrl')
            else:
                image = str(first_img)
        
        return {
            "name": get_value('name', 'title'),
            "brand": brand,
            "sku": get_value('sku'),
            "gtin": get_value('gtin13', 'gtin12', 'gtin14', 'gtin', 'mpn'),
            "url": get_value('url'),
            "image": image,
            "description": description,
            "price": (offers or {}).get('price'),
            "priceCurrency": (offers or {}).get('priceCurrency'),
            "availability": (offers or {}).get('availability'),
            "_raw": product_data,
        }
    
    async def _fetch_page(self, session: aiohttp.ClientSession, url: str):
        """Fetch a single page."""
        try:
            async with session.get(url, timeout=self.TIMEOUT) as resp:
                if resp.status != 200:
                    return None, None
                ctype = resp.headers.get("content-type", "")
                if not self.ALLOWED_CONTENT_RE.search(ctype):
                    return None, None
                html = await resp.text(errors="ignore")
                return html, str(resp.url)
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
            return None, None
    
    def _extract_products_from_html(self, html: str, url: str) -> List[dict]:
        """Extract products from HTML using structured data."""
        base = get_base_url(html, url)
        data = extruct_extract(html, base_url=base, syntaxes=['json-ld', 'microdata', 'rdfa'])
        products = []
        
        # JSON-LD
        for block in data.get('json-ld', []):
            items = block if isinstance(block, list) else [block]
            for item in items:
                nodes = item.get('@graph', []) if isinstance(item, dict) else []
                if nodes:
                    products += [n for n in nodes if isinstance(n, dict) and self._is_product_like(n)]
                elif isinstance(item, dict) and self._is_product_like(item):
                    products.append(item)
        
        # Microdata/RDFa
        for md in data.get('microdata', []):
            if isinstance(md, dict) and self._is_product_like(md):
                products.append(md)
        for r in data.get('rdfa', []):
            if isinstance(r, dict) and self._is_product_like(r):
                products.append(r)
        
        return [self._normalize_product(p) for p in products]
    
    async def _crawl(self, start_url: str, max_pages: int = 200) -> List[dict]:
        """Crawl website and extract products."""
        start_url = self._canonicalize(start_url)
        seen = set([start_url])
        queue = deque([(start_url, 0)])
        results = []
        
        conn = aiohttp.TCPConnector(limit=self.CONCURRENCY)
        async with aiohttp.ClientSession(
            headers={"User-Agent": self.USER_AGENT}, 
            connector=conn
        ) as session:
            
            pages_crawled = 0
            while queue and pages_crawled < max_pages:
                batch = []
                # Process URLs in batches (prioritizing product pages)
                while queue and len(batch) < self.CONCURRENCY:
                    batch.append(queue.popleft())
                
                tasks = [self._fetch_page(session, u) for (u, _) in batch]
                pages = await asyncio.gather(*tasks)
                pages_crawled += len(batch)
                
                for (html, final_url), (u, d) in zip(pages, batch):
                    if not html:
                        logger.debug(f"No HTML for {u}")
                        continue
                    
                    logger.debug(f"Processing {final_url} (depth {d})")
                    
                    # Extract products from current page
                    products = self._extract_products_from_html(html, final_url)
                    if products:
                        for p in products:
                            p.setdefault("sourceUrl", final_url)
                        results.extend(products)
                        logger.info(f"Found {len(products)} products from {final_url}")
                    else:
                        # Debug: Log when no products found on individual pages
                        page_type = self._classify_url(final_url)
                        if page_type == "product":
                            logger.warning(f"No products found on product page: {final_url}")
                    
                    # If this is a listing page, extract product links (regardless of whether we found products)
                    page_type = self._classify_url(final_url)
                    if page_type == "listing":
                        product_links = self._extract_product_links_from_listing(html, final_url)
                        logger.info(f"Extracted {len(product_links)} product links from listing page {final_url}")
                        
                        # Add product links to queue with higher priority
                        for product_url in product_links[:20]:  # Limit to avoid overwhelming
                            if product_url not in seen:
                                seen.add(product_url)
                                queue.appendleft((product_url, d + 1))  # Add to front for priority
                    
                    # Stop if max depth reached
                    if d >= self.MAX_DEPTH:
                        continue
                    
                    # Find new links to crawl (general navigation)
                    soup = BeautifulSoup(html, "html.parser")
                    links = [a.get("href") for a in soup.find_all("a")]
                    
                    # Filter and prioritize links
                    next_urls = []
                    for href in links:
                        if not self._is_candidate_link(href, final_url):
                            continue
                        url = self._canonicalize(urljoin(final_url, href))
                        if url in seen:
                            continue
                        seen.add(url)
                        next_urls.append(url)
                    
                    # Sort by priority (products first, then listings, then others)
                    next_urls.sort(key=lambda x: {"product": 0, "listing": 1, "other": 2}[self._classify_url(x)])
                    
                    # Limit general navigation links to avoid too much crawling
                    for url in next_urls[:10]:  # Reduced from unlimited to 10
                        queue.append((url, d + 1))
        
        logger.info(f"Crawl complete. Found {len(results)} total products from {len(seen)} pages")
        return results
    
    def _convert_to_schema_org_product(self, normalized_product: dict) -> SchemaOrgProduct:
        """Convert normalized product dict to SchemaOrgProduct object."""
        # Build schema.org compatible structure
        schema_data = {
            "@type": "Product"
        }
        
        # Map normalized fields to schema.org
        if normalized_product.get("name"):
            schema_data["name"] = normalized_product["name"]
        
        if normalized_product.get("description"):
            schema_data["description"] = normalized_product["description"]
        
        if normalized_product.get("sku"):
            schema_data["sku"] = str(normalized_product["sku"])
        
        if normalized_product.get("gtin"):
            schema_data["gtin"] = str(normalized_product["gtin"])
        
        if normalized_product.get("url"):
            schema_data["url"] = normalized_product["url"]
        
        if normalized_product.get("image"):
            schema_data["image"] = normalized_product["image"]
        
        # Handle brand
        if normalized_product.get("brand"):
            schema_data["brand"] = {
                "@type": "Brand",
                "name": normalized_product["brand"]
            }
        
        # Handle offers/pricing
        if normalized_product.get("price") or normalized_product.get("priceCurrency"):
            offers = {"@type": "Offer"}
            if normalized_product.get("price"):
                offers["price"] = str(normalized_product["price"])
            if normalized_product.get("priceCurrency"):
                offers["priceCurrency"] = normalized_product["priceCurrency"]
            if normalized_product.get("availability"):
                offers["availability"] = normalized_product["availability"]
            schema_data["offers"] = offers
        
        return SchemaOrgProduct(**schema_data)
    
    async def extract_from_url_and_links(self, url: str, max_links: int = 10) -> List[SchemaOrgProduct]:
        """
        Extract products from a URL using intelligent crawling.
        
        This method maintains compatibility with the original interface while using
        the new crawler-based approach.
        
        Args:
            url: The main URL to scrape
            max_links: Maximum number of pages to crawl (maps to max_pages)
            
        Returns:
            List of SchemaOrgProduct objects
        """
        try:
            logger.info(f"Starting intelligent crawl of {url} (max {max_links} pages)")
            
            # Use the crawler to extract products
            # Map max_links to max_pages (reasonable conversion)
            max_pages = min(max_links * 10, 200)  # Allow more pages for better discovery
            
            normalized_products = await self._crawl(url, max_pages)
            
            # Convert normalized products to SchemaOrgProduct objects
            schema_products = []
            for normalized_product in normalized_products:
                try:
                    schema_product = self._convert_to_schema_org_product(normalized_product)
                    schema_products.append(schema_product)
                except Exception as e:
                    logger.debug(f"Failed to convert product to schema.org format: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(schema_products)} products from {url}")
            return schema_products
            
        except Exception as e:
            logger.error(f"Failed to extract products from {url}: {e}")
            return []
    
    async def cleanup(self):
        """Clean up resources - no cleanup needed for this implementation"""
        pass

