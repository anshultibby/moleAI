"""HTML heuristic product extractor"""

import re
from typing import List, Optional
from loguru import logger
from bs4 import BeautifulSoup, Tag

from app.models.product import Product
from .base import BaseProductExtractor, ProductExtractionError

# HTML heuristic selectors
PRODUCT_LINK_SELECTORS = [
    'a[href*="/products/"]',
    'a[data-product-url]',
    '[data-product-id] a'
]

PRODUCT_CONTAINER_SELECTORS = [
    '.product-item',
    '.grid-product',
    '.product-grid-item',
    '.product-card',
    '[data-product-id]',
    '.product'
]

PRICE_SELECTORS = [
    '.price',
    '[itemprop="price"]',
    '[data-price]',
    '.money',
    '.product-price',
    '.price-current',
    '.price-regular',
    '.price-sale'
]

IMAGE_SELECTORS = [
    'img[src*="product"]',
    '.product-image img',
    '[data-product-image]',
    'img[alt*="product" i]',
    '.product img',
    '.grid-product img'
]

TITLE_SELECTORS = [
    '.product-title',
    '.product-name',
    '[data-product-title]',
    'h2',
    'h3',
    '.title',
    '.name'
]

VENDOR_SELECTORS = [
    '.product-vendor',
    '.brand',
    '.vendor',
    '[data-vendor]',
    '.product-brand'
]


class HtmlHeuristicExtractor(BaseProductExtractor):
    """Extract products using HTML heuristics and CSS selectors"""
    
    def extract_products(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract product data using HTML heuristics and CSS selectors.
        
        Args:
            html_content: The HTML content to extract from
            url: Base URL for resolving relative links
            
        Returns:
            List of Product instances
        """
        try:
            logger.info(f"Extracting products using HTML heuristics {'for ' + url if url else ''}")
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Find product containers
            products_from_containers = self._extract_from_product_containers(soup, url)
            
            # Method 2: Find product links
            products_from_links = self._extract_from_product_links(soup, url)
            
            # Combine and deduplicate
            all_products = products_from_containers + products_from_links
            unique_products = self._deduplicate_products(all_products)
            
            logger.info(f"Successfully extracted {len(unique_products)} products using HTML heuristics")
            return unique_products
            
        except Exception as e:
            error_msg = f"Failed to extract products using HTML heuristics: {str(e)}"
            logger.error(error_msg)
            raise ProductExtractionError(error_msg)
    
    def _extract_from_product_containers(self, soup: BeautifulSoup, base_url: str = "") -> List[Product]:
        """Extract products from product container elements."""
        products = []
        
        for selector in PRODUCT_CONTAINER_SELECTORS:
            containers = soup.select(selector)
            
            for container in containers:
                try:
                    product = self._extract_product_from_container(container, base_url)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Failed to extract product from container: {e}")
                    continue
        
        logger.debug(f"Found {len(products)} products from containers")
        return products
    
    def _extract_from_product_links(self, soup: BeautifulSoup, base_url: str = "") -> List[Product]:
        """Extract products from product link elements."""
        products = []
        
        for selector in PRODUCT_LINK_SELECTORS:
            links = soup.select(selector)
            
            for link in links:
                try:
                    product = self._extract_product_from_link(link, base_url)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Failed to extract product from link: {e}")
                    continue
        
        logger.debug(f"Found {len(products)} products from links")
        return products
    
    def _extract_product_from_container(self, container: Tag, base_url: str = "") -> Optional[Product]:
        """Extract product data from a product container element."""
        # Extract title
        title = self._extract_text_from_selectors(container, TITLE_SELECTORS)
        
        # Extract price
        price_text = self._extract_text_from_selectors(container, PRICE_SELECTORS)
        price, currency = self._parse_price_text(price_text)
        
        # Extract vendor/brand
        vendor = self._extract_text_from_selectors(container, VENDOR_SELECTORS)
        
        # Extract image URL
        image_url = self._extract_image_url(container)
        
        # Extract product URL
        product_url = self._extract_product_url(container)
        
        # Extract product ID from data attributes or URL
        product_id = (
            container.get('data-product-id') or
            container.get('data-id') or
            self.extract_product_id_from_url(product_url)
        )
        
        # Extract SKU if available
        sku = container.get('data-sku') or container.get('data-product-sku')
        
        return self.create_product_from_data(
            title=title,
            price=price,
            currency=currency,
            vendor=vendor,
            sku=sku,
            image_url=image_url,
            product_id=product_id,
            product_url=product_url,
            base_url=base_url
        )
    
    def _extract_product_from_link(self, link: Tag, base_url: str = "") -> Optional[Product]:
        """Extract product data from a product link element."""
        # Extract product URL
        product_url = link.get('href')
        
        # Extract title from link text or nearby elements
        title = (
            link.get_text(strip=True) or
            link.get('title') or
            link.get('aria-label')
        )
        
        # If title is empty, look for title in parent or nearby elements
        if not title:
            parent = link.parent
            if parent:
                title = self._extract_text_from_selectors(parent, TITLE_SELECTORS)
        
        # Extract product ID
        product_id = (
            link.get('data-product-id') or
            self.extract_product_id_from_url(product_url)
        )
        
        # Look for price in parent container
        price, currency = None, None
        if link.parent:
            price_text = self._extract_text_from_selectors(link.parent, PRICE_SELECTORS)
            price, currency = self._parse_price_text(price_text)
        
        return self.create_product_from_data(
            title=title,
            price=price,
            currency=currency,
            product_id=product_id,
            product_url=product_url,
            base_url=base_url
        )
    
    def _extract_text_from_selectors(self, container: Tag, selectors: List[str]) -> Optional[str]:
        """Extract text content using a list of CSS selectors."""
        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _extract_image_url(self, container: Tag) -> Optional[str]:
        """Extract image URL from container."""
        for selector in IMAGE_SELECTORS:
            img = container.select_one(selector)
            if img:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    return src
        return None
    
    def _extract_product_url(self, container: Tag) -> Optional[str]:
        """Extract product URL from container."""
        # Look for product links within the container
        for selector in PRODUCT_LINK_SELECTORS:
            link = container.select_one(selector)
            if link:
                href = link.get('href')
                if href:
                    return href
        
        # Fallback: look for any link that might be a product link
        links = container.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if href and '/products/' in href:
                return href
        
        return None
    
    def _parse_price_text(self, price_text: str) -> tuple[Optional[float], Optional[str]]:
        """Parse price text to extract amount and currency."""
        if not price_text:
            return None, None
        
        # Clean the price text
        cleaned_price = self.clean_price_string(price_text)
        
        if not cleaned_price:
            return None, None
        
        try:
            price = float(cleaned_price)
            # Try to detect currency from original text
            currency = self._detect_currency(price_text)
            return price, currency
        except ValueError:
            return None, None
    
    def _detect_currency(self, price_text: str) -> Optional[str]:
        """Detect currency from price text."""
        currency_symbols = {
            '$': 'USD',
            '€': 'EUR',
            '£': 'GBP',
            '¥': 'JPY',
            '₹': 'INR'
        }
        
        for symbol, code in currency_symbols.items():
            if symbol in price_text:
                return code
        
        # Look for currency codes
        currency_codes = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'CAD', 'AUD']
        for code in currency_codes:
            if code in price_text.upper():
                return code
        
        return 'USD'  # Default fallback
    
    def _deduplicate_products(self, products: List[Product]) -> List[Product]:
        """Remove duplicate products based on product_id or title."""
        seen = set()
        unique_products = []
        
        for product in products:
            # Create a key for deduplication
            key = product.product_id or product.title
            if key and key not in seen:
                seen.add(key)
                unique_products.append(product)
        
        return unique_products
