"""Base extractor class with common functionality"""

import re
import html
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger

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
        Normalize image URL to be absolute.
        
        Args:
            image_url: Raw image URL
            base_url: Base URL for relative URLs
            
        Returns:
            Normalized absolute URL or None
        """
        if not image_url:
            return None
        
        # Handle protocol-relative URLs
        if image_url.startswith('//'):
            return 'https:' + image_url
        
        # Handle relative URLs
        if image_url.startswith('/') and base_url:
            from urllib.parse import urljoin
            return urljoin(base_url, image_url)
        
        # Already absolute or no base URL to work with
        return image_url
    
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
                                base_url: str = "") -> Optional[Product]:
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
                variant_id=variant_id
            )
            return product
            
        except Exception as e:
            logger.error(f"Error creating product from data: {e}")
            return None
