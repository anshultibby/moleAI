"""Shopify analytics blob product extractor"""

import re
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from bs4 import BeautifulSoup

from app.models.product import Product
from .base import BaseProductExtractor, ProductExtractionError

# Constants for Shopify analytics detection
SHOPIFY_ANALYTICS_INDICATORS = [
    'collection_viewed',
    'productVariants',
    'web_pixels_manager',
    'analytics.track',
    'shopify.analytics',
    'product_viewed'
]

# Regex patterns for extracting product data
COLLECTION_PATTERNS = [
    r'collection_viewed["\']?\s*,\s*({.*?})',
    r'collection_viewed.*?({.*?})',
]

PRODUCT_VARIANTS_PATTERNS = [
    r'"productVariants"\s*:\s*(\[.*?\])',
    r'productVariants.*?(\[.*?\])',
]

PRODUCT_VIEWED_PATTERN = r'product_viewed["\']?\s*,\s*({.*?})'

# JSON-LD script type
JSON_LD_TYPE = 'application/ld+json'


class ShopifyAnalyticsExtractor(BaseProductExtractor):
    """Extract products from Shopify analytics blob (fast path)"""
    
    def extract_products(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract product data from Shopify pages using the analytics blob.
        
        Args:
            html_content: The HTML content of the Shopify page
            url: Optional URL for logging purposes
            
        Returns:
            List of Product instances
        """
        try:
            logger.info(f"Extracting Shopify products from analytics blob {'for ' + url if url else ''}")
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find analytics script containing product data
            analytics_script = self._find_analytics_script(soup)
            if not analytics_script:
                logger.warning("No Shopify analytics script found")
                return []
            
            # Extract product variants from the script
            product_variants = self._extract_product_variants(analytics_script)
            if not product_variants:
                logger.warning("No product variants found in analytics script")
                return []
            
            # Convert to Product instances
            products = []
            for variant in product_variants:
                try:
                    product = self._create_shopify_product(variant, url)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to create product from variant: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(products)} products from Shopify analytics")
            return products
            
        except Exception as e:
            error_msg = f"Failed to extract Shopify products: {str(e)}"
            logger.error(error_msg)
            raise ProductExtractionError(error_msg)
    
    def _find_analytics_script(self, soup: BeautifulSoup) -> Optional[str]:
        """Find the Shopify analytics script containing product data."""
        # Look for script tags that might contain analytics data
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if not script.string:
                continue
                
            script_content = script.string.strip()
            
            # Check if script contains any analytics indicators
            for indicator in SHOPIFY_ANALYTICS_INDICATORS:
                if indicator in script_content:
                    logger.debug(f"Found analytics script with indicator: {indicator}")
                    return script_content
        
        # Also check for JSON-LD structured data as fallback
        json_ld_scripts = soup.find_all('script', {'type': JSON_LD_TYPE})
        for script in json_ld_scripts:
            if script.string and 'Product' in script.string:
                logger.debug("Found JSON-LD product data as fallback")
                return script.string
        
        return None
    
    def _extract_product_variants(self, script_content: str) -> List[Dict[str, Any]]:
        """Extract product variants from the analytics script content."""
        product_variants = []
        
        try:
            # Method 1: Extract from collection_viewed events
            variants_from_collections = self._extract_from_collection_events(script_content)
            product_variants.extend(variants_from_collections)
            
            # Method 2: Extract from productVariants arrays
            variants_from_arrays = self._extract_from_product_variants_arrays(script_content)
            product_variants.extend(variants_from_arrays)
            
            # Method 3: Extract from individual product_viewed events
            variants_from_products = self._extract_from_product_events(script_content)
            product_variants.extend(variants_from_products)
            
            # Method 4: JSON-LD structured data fallback
            if not product_variants:
                variants_from_json_ld = self._extract_from_json_ld(script_content)
                product_variants.extend(variants_from_json_ld)
            
        except Exception as e:
            logger.error(f"Error extracting product variants: {e}")
        
        return product_variants
    
    def _extract_from_collection_events(self, script_content: str) -> List[Dict[str, Any]]:
        """Extract product variants from collection_viewed events."""
        product_variants = []
        
        for pattern in COLLECTION_PATTERNS:
            collection_matches = re.findall(pattern, script_content, re.DOTALL)
            
            for match in collection_matches:
                try:
                    clean_json = self.clean_json_string(match)
                    collection_data = json.loads(clean_json)
                    
                    # Extract products from collection data
                    if 'collection' in collection_data and 'productVariants' in collection_data['collection']:
                        variants = collection_data['collection']['productVariants']
                        if isinstance(variants, list):
                            product_variants.extend(variants)
                            logger.debug(f"Found {len(variants)} product variants via collection.productVariants")
                    elif 'productVariants' in collection_data:
                        variants = collection_data['productVariants']
                        if isinstance(variants, list):
                            product_variants.extend(variants)
                            logger.debug(f"Found {len(variants)} product variants via productVariants")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse collection_viewed JSON: {e}")
                    continue
        
        return product_variants
    
    def _extract_from_product_variants_arrays(self, script_content: str) -> List[Dict[str, Any]]:
        """Extract product variants from productVariants arrays."""
        product_variants = []
        
        for pattern in PRODUCT_VARIANTS_PATTERNS:
            variants_matches = re.findall(pattern, script_content, re.DOTALL)
            
            for match in variants_matches:
                try:
                    clean_json = self.clean_json_string(match)
                    variants_data = json.loads(clean_json)
                    if isinstance(variants_data, list):
                        product_variants.extend(variants_data)
                        logger.debug(f"Found {len(variants_data)} product variants via productVariants array")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse productVariants JSON: {e}")
                    continue
        
        return product_variants
    
    def _extract_from_product_events(self, script_content: str) -> List[Dict[str, Any]]:
        """Extract product variants from individual product_viewed events."""
        product_variants = []
        
        product_matches = re.findall(PRODUCT_VIEWED_PATTERN, script_content, re.DOTALL)
        
        for match in product_matches:
            try:
                product_data = json.loads(match)
                if 'productVariant' in product_data:
                    product_variants.append(product_data['productVariant'])
                elif 'product' in product_data:
                    # Convert product to variant format
                    product = product_data['product']
                    if 'variants' in product:
                        product_variants.extend(product['variants'])
                    else:
                        # Single variant product
                        product_variants.append(product)
                logger.debug("Found product variant via product_viewed event")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse product_viewed JSON: {e}")
        
        return product_variants
    
    def _extract_from_json_ld(self, script_content: str) -> List[Dict[str, Any]]:
        """Extract product variants from JSON-LD structured data."""
        product_variants = []
        
        try:
            # Try to parse entire script as JSON (for JSON-LD)
            json_data = json.loads(script_content)
            
            # Handle different JSON-LD structures
            if isinstance(json_data, dict):
                if json_data.get('@type') == 'Product':
                    product_variants.append(json_data)
                elif 'offers' in json_data:
                    # Extract from offers
                    offers = json_data['offers']
                    if isinstance(offers, list):
                        product_variants.extend(offers)
                    else:
                        product_variants.append(offers)
            elif isinstance(json_data, list):
                # Array of products
                for item in json_data:
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        product_variants.append(item)
            
            if product_variants:
                logger.debug(f"Found {len(product_variants)} products via JSON-LD fallback")
                
        except json.JSONDecodeError:
            # Not valid JSON, skip
            pass
        
        return product_variants
    
    def _create_shopify_product(self, variant_data: Dict[str, Any], source_url: str = "") -> Optional[Product]:
        """Create a Product instance from Shopify variant data."""
        try:
            # Handle nested product structure (common in Shopify analytics)
            product_info = variant_data.get('product', {})
            price_info = variant_data.get('price', {})
            
            # Extract title
            title = (
                product_info.get('title') or
                variant_data.get('title') or 
                variant_data.get('name') or 
                variant_data.get('product_title') or
                variant_data.get('productTitle')
            )
            
            # Extract and parse price
            price, currency = None, None
            if isinstance(price_info, dict):
                # Shopify analytics format: {"amount": 99.0, "currencyCode": "USD"}
                price = price_info.get('amount')
                currency = price_info.get('currencyCode')
            else:
                # Fallback to direct price field
                price_raw = variant_data.get('price')
                if price_raw is not None:
                    price, currency = Product.parse_price_and_currency(str(price_raw))
            
            # Extract vendor/brand
            vendor = (
                product_info.get('vendor') or
                variant_data.get('vendor') or 
                variant_data.get('brand') or
                variant_data.get('manufacturer')
            )
            
            # Extract SKU
            sku = variant_data.get('sku')
            
            # Extract image URL
            image_url = (
                variant_data.get('featured_image') or
                variant_data.get('image') or
                variant_data.get('image_url') or
                variant_data.get('imageUrl') or
                product_info.get('featured_image')
            )
            # Handle image URL - could be string or dict
            if isinstance(image_url, dict):
                # Sometimes image is an object with url property
                image_url = image_url.get('url') or image_url.get('src')
            
            # Extract IDs
            product_id = str(
                product_info.get('id') or
                variant_data.get('product_id') or 
                variant_data.get('productId') or 
                ''
            )
            variant_id = str(
                variant_data.get('id') or 
                variant_data.get('variant_id') or 
                variant_data.get('variantId') or 
                ''
            )
            
            # Extract product URL
            product_url = (
                product_info.get('url') or
                variant_data.get('url') or
                variant_data.get('product_url') or
                variant_data.get('productUrl')
            )
            
            # Use base class method to create product
            return self.create_product_from_data(
                title=title,
                price=price,
                currency=currency,
                vendor=vendor,
                sku=sku,
                image_url=image_url,
                product_id=product_id if product_id else None,
                variant_id=variant_id if variant_id else None,
                product_url=product_url,
                base_url=source_url
            )
            
        except Exception as e:
            logger.error(f"Error creating Shopify product from variant data: {e}")
            return None
