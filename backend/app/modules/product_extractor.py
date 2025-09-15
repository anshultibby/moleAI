"""Simplified product extraction module - JSON-LD only"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from loguru import logger
from bs4 import BeautifulSoup

from .direct_scraper import DirectScraper


class ProductExtractionError(Exception):
    """Custom exception for product extraction errors"""
    pass


class ProductExtractor:
    """
    Simplified product extractor that only extracts JSON-LD structured data
    and follows links to extract more products.
    """
    
    def __init__(self):
        """Initialize the product extractor"""
        self.scraper = DirectScraper()
    
    def extract_json_ld_products(self, html_content: str, url: str = "") -> List[str]:
        """
        Extract JSON-LD product cards as strings.
        
        Args:
            html_content: The HTML content to extract from
            url: Optional URL for context and logging
            
        Returns:
            List of JSON-LD product cards as strings
        """
        try:
            logger.info(f"Extracting JSON-LD products {'from ' + url if url else ''}")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            product_cards = []
            
            # Find all JSON-LD script tags
            json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            
            for script in json_ld_scripts:
                if not script.string:
                    continue
                    
                try:
                    data = json.loads(script.string)
                    products = self._extract_products_from_json_ld(data)
                    
                    # Save each product as a JSON string
                    for product in products:
                        product_cards.append(json.dumps(product, indent=2))
                        
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON-LD: {e}")
                    continue
            
            logger.info(f"Found {len(product_cards)} JSON-LD product cards")
            return product_cards
            
        except Exception as e:
            error_msg = f"JSON-LD extraction failed: {str(e)}"
            logger.error(error_msg)
            raise ProductExtractionError(error_msg)
    
    def _extract_products_from_json_ld(self, data: Any) -> List[Dict[str, Any]]:
        """Extract product objects from JSON-LD data"""
        products = []
        
        if isinstance(data, dict):
            # Direct Product type
            if data.get('@type') == 'Product':
                products.append(data)
            
            # ItemList containing products
            elif data.get('@type') == 'ItemList':
                items = data.get('itemListElement', [])
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        products.append(item)
            
            # Search for nested products
            else:
                for key, value in data.items():
                    if isinstance(value, dict) and value.get('@type') == 'Product':
                        products.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                products.append(item)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    products.extend(self._extract_products_from_json_ld(item))
        
        return products
    
    def get_page_links(self, html_content: str, base_url: str) -> List[str]:
        """
        Extract all links from the page that might contain products.
        
        Args:
            html_content: The HTML content to extract links from
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if not href:
                    continue
                
                # Convert to absolute URL
                absolute_url = urljoin(base_url, href)
                
                # Filter for product-like URLs
                if self._is_product_link(absolute_url):
                    links.append(absolute_url)
            
            # Remove duplicates while preserving order
            unique_links = []
            seen = set()
            for link in links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            logger.info(f"Found {len(unique_links)} product links")
            return unique_links
            
        except Exception as e:
            logger.error(f"Failed to extract links: {e}")
            return []
    
    def _is_product_link(self, url: str) -> bool:
        """Check if URL looks like a product page"""
        if not url:
            return False
        
        # Skip external links
        parsed_base = urlparse(url)
        if not parsed_base.netloc:
            return False
        
        # Skip common non-product paths
        skip_patterns = [
            '/cart', '/checkout', '/account', '/login', '/register',
            '/search', '/blog', '/about', '/contact', '/help',
            '/privacy', '/terms', '/shipping', '/returns',
            '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg',
            'mailto:', 'tel:', '#'
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Look for product-like patterns
        product_patterns = [
            '/product', '/item', '/p/', '/products/',
            '/shop', '/store', '/buy'
        ]
        
        for pattern in product_patterns:
            if pattern in url_lower:
                return True
        
        return False
    
    async def scrape_and_extract_with_links(self, 
                                           url: str, 
                                           max_links: int = 10,
                                           render_js: bool = True, 
                                           wait: int = 2000) -> Dict[str, List[str]]:
        """
        Scrape a URL and extract JSON-LD products from it and linked pages.
        
        Args:
            url: URL to scrape and extract products from
            max_links: Maximum number of links to follow (default: 10)
            render_js: Whether to render JavaScript (default: True)
            wait: Time to wait in milliseconds after page load (default: 2000ms)
            
        Returns:
            Dictionary with 'main_page' and 'linked_pages' containing product cards as strings
            
        Raises:
            ProductExtractionError: If scraping or extraction fails
        """
        try:
            logger.info(f"Scraping and extracting products from {url} and its links")
            
            # Step 1: Scrape the main page
            html_content = await self.scraper.scrape_url(
                url, 
                render_js=render_js, 
                wait=wait,
                smart_js_detection=True
            )
            
            # Step 2: Extract products from main page
            main_products = self.extract_json_ld_products(html_content, url)
            
            # Step 3: Get product links from the page
            product_links = self.get_page_links(html_content, url)
            
            # Limit the number of links to follow
            if len(product_links) > max_links:
                product_links = product_links[:max_links]
                logger.info(f"Limited to first {max_links} product links")
            
            # Step 4: Extract products from linked pages
            linked_products = []
            for link_url in product_links:
                try:
                    logger.info(f"Extracting from linked page: {link_url}")
                    
                    # Scrape the linked page
                    link_html = await self.scraper.scrape_url(
                        link_url,
                        render_js=render_js,
                        wait=wait,
                        smart_js_detection=True
                    )
                    
                    # Extract products from linked page
                    link_products = self.extract_json_ld_products(link_html, link_url)
                    linked_products.extend(link_products)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract from {link_url}: {e}")
                    continue
            
            result = {
                'main_page': main_products,
                'linked_pages': linked_products
            }
            
            total_products = len(main_products) + len(linked_products)
            logger.info(f"Successfully extracted {total_products} total products ({len(main_products)} from main page, {len(linked_products)} from {len(product_links)} linked pages)")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to scrape and extract products from {url}: {str(e)}"
            logger.error(error_msg)
            raise ProductExtractionError(error_msg)
        finally:
            # Clean up scraper resources
            await self.scraper.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'scraper'):
            await self.scraper.cleanup()

