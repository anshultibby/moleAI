"""Base extractor class with common functionality"""

import re
import html
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger
from bs4 import BeautifulSoup

from app.models.product import Product


class ProductExtractionError(Exception):
    """Custom exception for product extraction-related errors"""
    pass


class BaseProductExtractor(ABC):
    """Base class for product extractors with common functionality"""
    
    def __init__(self):
        """Initialize the base extractor"""
        pass
    
    @abstractmethod
    def extract_products(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract products from HTML content.
        
        Args:
            html_content: The HTML content to extract from
            url: Optional source URL for context
            
        Returns:
            List of Product instances
        """
        pass
    
    def clean_json_string(self, json_string: str) -> str:
        """
        Clean and prepare JSON string for parsing.
        
        Args:
            json_string: Raw JSON string that may contain HTML entities or escaped quotes
            
        Returns:
            Cleaned JSON string ready for parsing
        """
        # Decode HTML entities and unescape backslashes
        clean_json = html.unescape(json_string)
        clean_json = clean_json.replace('\\"', '"').replace('\\\\', '\\')
        return clean_json
    
    def clean_price_string(self, price_string: str) -> str:
        """
        Clean price string by removing currency symbols and formatting.
        
        Args:
            price_string: Raw price string like "$99.00" or "99,99 €"
            
        Returns:
            Cleaned numeric string
        """
        if not price_string:
            return ""
        
        # Remove common currency symbols and formatting
        cleaned = re.sub(r'[^\d.,]', '', str(price_string))
        # Handle European decimal format (99,99 -> 99.99)
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')
        # Remove thousands separators if present (1,999.99 -> 1999.99)
        elif ',' in cleaned and '.' in cleaned:
            parts = cleaned.split('.')
            if len(parts) == 2 and len(parts[1]) <= 2:  # Decimal part
                cleaned = parts[0].replace(',', '') + '.' + parts[1]
        
        return cleaned
    
    def normalize_image_url(self, image_url: str, base_url: str = "") -> Optional[str]:
        """
        Normalize image URL to be absolute and validate it.
        
        Args:
            image_url: Raw image URL
            base_url: Base URL for relative URLs
            
        Returns:
            Normalized absolute URL or None if invalid
        """
        if not image_url:
            return None
        
        # Skip placeholder, broken, or invalid image URLs
        if self._is_invalid_image_url(image_url):
            return None
        
        # Handle protocol-relative URLs
        if image_url.startswith('//'):
            normalized_url = 'https:' + image_url
        # Handle relative URLs
        elif image_url.startswith('/') and base_url:
            from urllib.parse import urljoin
            normalized_url = urljoin(base_url, image_url)
        else:
            # Already absolute or no base URL to work with
            normalized_url = image_url
        
        # Final validation of the normalized URL
        if self._is_invalid_image_url(normalized_url):
            return None
            
        return normalized_url
    
    def _is_invalid_image_url(self, url: str) -> bool:
        """
        Check if an image URL is invalid or a placeholder.
        
        Args:
            url: Image URL to validate
            
        Returns:
            True if the URL should be skipped
        """
        if not url:
            return True
            
        # Convert to lowercase for case-insensitive checks
        url_lower = url.lower()
        
        # Skip common placeholder patterns
        invalid_patterns = [
            'placeholder',
            'no-image',
            'noimage',
            'default',
            'missing',
            'unavailable',
            'coming-soon',
            'example.com',
            'lorem',
            'dummy',
            'blank',
            'empty',
            '1x1',
            'spacer',
            'transparent',
            'pixel.gif',
            'clear.gif',
            'data:image/gif;base64,r0lgodlhaqabaiaaap', # 1x1 transparent gif
        ]
        
        # Check for invalid patterns
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return True
        
        # Skip very small images (likely placeholders)
        if any(dim in url_lower for dim in ['1x1', '2x2', '5x5', '10x10']):
            return True
        
        # Skip data URLs that are too short (likely placeholders)
        if url.startswith('data:') and len(url) < 100:
            return True
        
        # Basic URL format validation
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return True
        except:
            return True
        
        return False
    
    async def fetch_product_page_image(self, product_url: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
        """
        Fetch the main product image from a product page URL.
        
        Args:
            product_url: URL of the product page
            session: Optional aiohttp session to reuse
            
        Returns:
            Best quality image URL from the product page or None
        """
        if not product_url:
            return None
            
        # Create session if not provided
        close_session = False
        if session is None:
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            )
            close_session = True
        
        try:
            async with session.get(product_url) as response:
                if response.status != 200:
                    return None
                    
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract the best image from the product page
                image_url = self._extract_main_product_image(soup, product_url)
                
                if image_url:
                    # Normalize and validate the image URL
                    return self.normalize_image_url(image_url, product_url)
                
                return None
                
        except Exception as e:
            logger.debug(f"Failed to fetch product page image from {product_url}: {e}")
            return None
        finally:
            if close_session:
                await session.close()
    
    def _extract_main_product_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        Extract the main product image from a product page.
        Prioritizes high-quality images typically found on product detail pages.
        
        Args:
            soup: BeautifulSoup object of the product page
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Best image URL found or None
        """
        # Priority selectors for product detail pages (higher quality images)
        MAIN_IMAGE_SELECTORS = [
            # Schema.org structured data
            '[itemprop="image"]',
            # Open Graph meta tags
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            # Common product image containers
            '.product-image img',
            '.main-image img',
            '.hero-image img',
            '.primary-image img',
            '.featured-image img',
            '.product-photo img',
            '.product-gallery img:first-child',
            '.image-gallery img:first-child',
            # Shopify specific
            '.product__media img',
            '.product-single__media img',
            # WooCommerce specific
            '.woocommerce-product-gallery__image img',
            # Magento specific
            '.product-image-main img',
            # Generic high-priority selectors
            'img[src*="product"]',
            'img[alt*="product" i]',
            'img[data-zoom]',
            'img[data-large]',
            'main img',
            '.content img',
            'img'
        ]
        
        image_candidates = []
        
        # Check meta tags first (often highest quality)
        for meta_selector in ['meta[property="og:image"]', 'meta[name="twitter:image"]']:
            meta_tag = soup.select_one(meta_selector)
            if meta_tag:
                content = meta_tag.get('content')
                if content:
                    image_candidates.append((content, 10.0))  # High priority for meta tags
        
        # Check other selectors
        for selector in MAIN_IMAGE_SELECTORS:
            elements = soup.select(selector)
            for element in elements:
                if element.name == 'meta':
                    src = element.get('content')
                else:
                    src = (element.get('src') or 
                          element.get('data-src') or 
                          element.get('data-original') or 
                          element.get('data-zoom') or
                          element.get('data-large'))
                
                if src:
                    # Calculate quality score for product page images
                    quality_score = self._calculate_product_page_image_score(element, src)
                    image_candidates.append((src, quality_score))
        
        # Sort by quality score and return the best one
        if image_candidates:
            image_candidates.sort(key=lambda x: x[1], reverse=True)
            return image_candidates[0][0]
        
        return None
    
    def _calculate_product_page_image_score(self, element, src: str) -> float:
        """Calculate quality score for images on product detail pages"""
        score = 0.0
        src_lower = src.lower()
        
        # Higher base score for product pages (we expect better images)
        score += 5.0
        
        # Prefer larger image dimensions
        if any(size in src_lower for size in ['1200x', '1000x', '800x', 'large', 'xlarge', 'master']):
            score += 5.0
        elif any(size in src_lower for size in ['600x', '500x', 'medium']):
            score += 3.0
        elif any(size in src_lower for size in ['400x', '300x']):
            score += 1.0
        elif any(size in src_lower for size in ['200x', '150x', '100x', 'thumb', 'small']):
            score -= 2.0
        
        # Prefer main/primary image indicators
        if any(keyword in src_lower for keyword in ['main', 'primary', 'hero', 'featured', 'gallery']):
            score += 3.0
        
        # Prefer product-specific URLs
        if any(keyword in src_lower for keyword in ['product', 'item', 'catalog']):
            score += 2.0
        
        # Check element attributes for quality indicators
        if hasattr(element, 'get'):
            # Zoom/large data attributes suggest high quality
            if element.get('data-zoom') or element.get('data-large'):
                score += 4.0
            
            # Alt text quality
            alt_text = (element.get('alt') or '').lower()
            if alt_text and any(keyword in alt_text for keyword in ['product', 'main', 'primary']):
                score += 2.0
        
        # Penalize obvious thumbnails or placeholders
        if any(pattern in src_lower for pattern in ['thumb', 'placeholder', 'loading', 'default']):
            score -= 3.0
        
        return score
    
    def normalize_product_url(self, product_url: str, base_url: str = "") -> Optional[str]:
        """
        Normalize product URL to be absolute.
        
        Args:
            product_url: Raw product URL
            base_url: Base URL for relative URLs
            
        Returns:
            Normalized absolute URL or None
        """
        if not product_url:
            return None
        
        # Handle relative URLs
        if product_url.startswith('/') and base_url:
            from urllib.parse import urljoin
            return urljoin(base_url, product_url)
        
        # Already absolute or no base URL to work with
        return product_url
    
    def extract_product_id_from_url(self, product_url: str) -> Optional[str]:
        """
        Extract product ID from Shopify product URL.
        
        Args:
            product_url: Product URL like "/products/product-name" or full URL
            
        Returns:
            Product handle/ID or None
        """
        if not product_url:
            return None
        
        # Extract product handle from URL
        match = re.search(r'/products/([^/?]+)', product_url)
        if match:
            return match.group(1)
        
        return None
    
    def create_product_from_data(self, 
                                title: Optional[str] = None,
                                price: Optional[float] = None,
                                currency: Optional[str] = None,
                                vendor: Optional[str] = None,
                                sku: Optional[str] = None,
                                image_url: Optional[str] = None,
                                product_id: Optional[str] = None,
                                variant_id: Optional[str] = None,
                                product_url: Optional[str] = None,
                                base_url: str = "",
                                # Enhanced attributes
                                product_type: Optional[str] = None,
                                color: Optional[str] = None,
                                size: Optional[str] = None,
                                material: Optional[str] = None,
                                tags: Optional[List[str]] = None,
                                color_variants: Optional[List[str]] = None,
                                size_variants: Optional[List[str]] = None,
                                variant_options: Optional[Dict[str, List[str]]] = None,
                                confidence_score: Optional[float] = None) -> Optional[Product]:
        """
        Create a Product instance from extracted data with validation.
        
        Args:
            title: Product title
            price: Product price as float
            currency: Price currency
            vendor: Product vendor/brand
            sku: Product SKU
            image_url: Product image URL
            product_id: Product ID
            variant_id: Variant ID
            product_url: Product page URL
            base_url: Base URL for normalizing relative URLs
            product_type: Product type/category
            color: Primary color of this variant
            size: Size of this variant
            material: Material/fabric information
            tags: Product tags/categories
            color_variants: Available color options
            size_variants: Available size options
            variant_options: All variant options
            confidence_score: Confidence score for the extraction (0.0-1.0)
            
        Returns:
            Product instance or None if essential data is missing
        """
        try:
            # Normalize URLs
            normalized_image_url = self.normalize_image_url(image_url, base_url)
            normalized_product_url = self.normalize_product_url(product_url, base_url)
            
            # Extract product ID from URL if not provided
            if not product_id and normalized_product_url:
                product_id = self.extract_product_id_from_url(normalized_product_url)
            
            # Create Product directly - Pydantic validators handle cleaning and URL extraction
            product = Product(
                product_name=title,
                store=vendor,  # Will extract from product_url if None
                price=price,
                price_value=price,  # Will be auto-calculated from price string
                product_url=normalized_product_url,
                image_url=normalized_image_url,
                currency=currency or "USD",
                sku=sku,
                product_id=product_id,
                variant_id=variant_id,
                # Enhanced attributes
                product_type=product_type,
                color=color,
                size=size,
                material=material,
                tags=tags,
                color_variants=color_variants,
                size_variants=size_variants,
                variant_options=variant_options
            )
            
            # Add confidence score as attribute if provided
            if confidence_score is not None:
                product.confidence_score = confidence_score
            return product
            
        except Exception as e:
            logger.error(f"Error creating product from data: {e}")
            return None
