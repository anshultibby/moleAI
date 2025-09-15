"""
Simple JSON-LD Product Extractor

This module extracts product data from e-commerce sites by:
1. Finding JSON-LD structured data on pages
2. Following product links and extracting from those pages in parallel
3. Returning product data as JSON strings
"""

import asyncio
import json
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger

from .direct_scraper import DirectScraper
from app.models.product import SchemaOrgProduct


class ProductExtractor:
    """
    Simple product extractor that only looks for JSON-LD data.
    
    Usage:
        extractor = ProductExtractor()
        result = await extractor.extract_from_url_and_links(url)
        print(f"Found {len(result['products'])} products")
    """
    
    def __init__(self):
        self.scraper = DirectScraper()
    
    def find_json_ld_products(self, html: str) -> List[SchemaOrgProduct]:
        """
        Find all JSON-LD products in HTML and return them as SchemaOrgProduct objects.
        
        Args:
            html: HTML content to search
            
        Returns:
            List of SchemaOrgProduct objects
        """
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # Find all JSON-LD script tags
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            if not script.string:
                continue
                
            try:
                data = json.loads(script.string)
                found_products = self._find_products_in_data(data)
                
                # Convert each product dict to SchemaOrgProduct
                for product_data in found_products:
                    try:
                        product = SchemaOrgProduct(**product_data)
                        products.append(product)
                    except Exception as e:
                        logger.debug(f"Failed to parse product data: {e}")
                        continue
                    
            except json.JSONDecodeError:
                continue  # Skip invalid JSON
        
        return products
    
    def _find_products_in_data(self, data) -> List[Dict]:
        """
        Recursively find all Product objects in JSON-LD data.
        
        Args:
            data: JSON-LD data (dict, list, or other)
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        if isinstance(data, dict):
            # Check if this is a Product
            if data.get('@type') == 'Product':
                products.append(data)
            
            # Check if this is an ItemList with products
            elif data.get('@type') == 'ItemList':
                for item in data.get('itemListElement', []):
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        products.append(item)
            
            # Search all values for more products
            else:
                for value in data.values():
                    products.extend(self._find_products_in_data(value))
        
        elif isinstance(data, list):
            # Search each item in the list
            for item in data:
                products.extend(self._find_products_in_data(item))
        
        return products
    
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
        Scrape multiple URLs in parallel and extract JSON-LD products.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of SchemaOrgProduct objects from all URLs
        """
        if not urls:
            return []
        
        async def scrape_one_url(url: str) -> List[SchemaOrgProduct]:
            """Scrape a single URL and return its products"""
            try:
                scraper = DirectScraper()
                try:
                    html = await scraper.scrape_url(url, render_js=True, wait=2000, smart_js_detection=True)
                    products = self.find_json_ld_products(html)
                    logger.info(f"Found {len(products)} products from {url}")
                    return products
                finally:
                    await scraper.cleanup()
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")
                return []
        
        # Scrape all URLs in parallel
        logger.info(f"Scraping {len(urls)} URLs in parallel...")
        tasks = [scrape_one_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all products
        all_products = []
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
        
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

