"""General product extractor using layered approach"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from bs4 import BeautifulSoup, Tag

from app.models.product import Product
from .base import BaseProductExtractor, ProductExtractionError


class GeneralProductExtractor(BaseProductExtractor):
    """
    General product extractor using a layered approach:
    1. JSON-LD structured data (most reliable)
    2. Microdata/RDFa (schema.org markup)
    3. CSS heuristics (fallback)
    """
    
    # Common CSS selectors for fallback extraction
    PRODUCT_CONTAINER_SELECTORS = [
        '[itemtype*="schema.org/Product"]',
        '[data-product-id]',
        '.product-item',
        '.product-card',
        '.product-tile',
        '.product-grid-item',
        '.grid-product',
        '.product'
    ]
    
    TITLE_SELECTORS = [
        '[itemprop="name"]',
        '.product-title',
        '.product-name',
        '[data-product-title]',
        'h1', 'h2', 'h3',
        '.title',
        '.name'
    ]
    
    PRICE_SELECTORS = [
        '[itemprop="price"]',
        '[itemprop="lowPrice"]',
        '[data-price]',
        '.price',
        '.money',
        '.product-price',
        '.price-current',
        '.price-regular',
        '.price-sale',
        '.amount'
    ]
    
    IMAGE_SELECTORS = [
        '[itemprop="image"]',
        'img[src*="product"]',
        '.product-image img',
        '[data-product-image]',
        'img[alt*="product" i]',
        '.product img',
        'img'
    ]
    
    BRAND_SELECTORS = [
        '[itemprop="brand"]',
        '.product-vendor',
        '.brand',
        '.vendor',
        '[data-vendor]',
        '.product-brand'
    ]
    
    def extract_products(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract products using layered approach
        
        Args:
            html_content: The HTML content to extract from
            url: Base URL for resolving relative links
            
        Returns:
            List of Product instances with confidence scores
        """
        try:
            logger.info(f"Extracting products using general layered approach {'for ' + url if url else ''}")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            all_products = []
            
            # Layer 1: JSON-LD structured data (highest confidence)
            json_ld_products = self._extract_from_json_ld(soup, url)
            all_products.extend(json_ld_products)
            logger.debug(f"Found {len(json_ld_products)} products from JSON-LD")
            
            # Layer 2: Microdata (medium confidence)
            microdata_products = self._extract_from_microdata(soup, url)
            all_products.extend(microdata_products)
            logger.debug(f"Found {len(microdata_products)} products from microdata")
            
            # Layer 3: CSS heuristics (lower confidence)
            if not all_products:  # Only use fallback if no structured data found
                heuristic_products = self._extract_from_css_heuristics(soup, url)
                all_products.extend(heuristic_products)
                logger.debug(f"Found {len(heuristic_products)} products from CSS heuristics")
            
            # Deduplicate and sort by confidence
            unique_products = self._deduplicate_and_rank(all_products)
            
            logger.info(f"Successfully extracted {len(unique_products)} products using general approach")
            return unique_products
            
        except Exception as e:
            error_msg = f"Failed to extract products using general approach: {str(e)}"
            logger.error(error_msg)
            raise ProductExtractionError(error_msg)
    
    def _extract_from_json_ld(self, soup: BeautifulSoup, base_url: str = "") -> List[Product]:
        """Extract products from JSON-LD structured data"""
        products = []
        
        # Find all JSON-LD script tags
        json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        
        for script in json_ld_scripts:
            if not script.string:
                continue
                
            try:
                data = json.loads(script.string)
                
                # Handle different JSON-LD structures
                if isinstance(data, dict):
                    products.extend(self._parse_json_ld_object(data, base_url))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            products.extend(self._parse_json_ld_object(item, base_url))
                            
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON-LD: {e}")
                continue
        
        return products
    
    def _parse_json_ld_object(self, data: Dict[str, Any], base_url: str = "") -> List[Product]:
        """Parse a single JSON-LD object for products"""
        products = []
        
        # Direct Product type
        if data.get('@type') == 'Product':
            product = self._create_product_from_json_ld(data, base_url)
            if product:
                products.append(product)
        
        # ItemList containing products
        elif data.get('@type') == 'ItemList':
            items = data.get('itemListElement', [])
            for item in items:
                if isinstance(item, dict) and item.get('@type') == 'Product':
                    product = self._create_product_from_json_ld(item, base_url)
                    if product:
                        products.append(product)
        
        # Search for nested products
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) and value.get('@type') == 'Product':
                    product = self._create_product_from_json_ld(value, base_url)
                    if product:
                        products.append(product)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            product = self._create_product_from_json_ld(item, base_url)
                            if product:
                                products.append(product)
        
        return products
    
    def _create_product_from_json_ld(self, data: Dict[str, Any], base_url: str = "") -> Optional[Product]:
        """Create Product from JSON-LD data"""
        try:
            # Extract basic fields
            title = data.get('name')
            
            # Extract price from offers
            price, currency = None, None
            offers = data.get('offers', data.get('offer'))
            if offers:
                if isinstance(offers, list):
                    offers = offers[0]  # Take first offer
                if isinstance(offers, dict):
                    price = offers.get('price') or offers.get('lowPrice')
                    currency = offers.get('priceCurrency')
                    
                    # Try to parse price if it's a string
                    if isinstance(price, str):
                        price, parsed_currency = Product.parse_price_and_currency(price)
                        if not currency:
                            currency = parsed_currency
            
            # Extract other fields
            brand = None
            brand_data = data.get('brand')
            if isinstance(brand_data, dict):
                brand = brand_data.get('name')
            elif isinstance(brand_data, str):
                brand = brand_data
            
            # Extract image
            image_url = None
            image_data = data.get('image')
            if isinstance(image_data, list) and image_data:
                image_url = image_data[0]
            elif isinstance(image_data, str):
                image_url = image_data
            elif isinstance(image_data, dict):
                image_url = image_data.get('url')
            
            # Extract URL
            product_url = data.get('url')
            
            # Extract SKU
            sku = data.get('sku') or data.get('mpn') or data.get('gtin')
            
            # Extract category/type
            category = data.get('category')
            if isinstance(category, list):
                category = category[0] if category else None
            
            return self.create_product_from_data(
                title=title,
                price=price,
                currency=currency,
                vendor=brand,
                sku=sku,
                image_url=image_url,
                product_url=product_url,
                base_url=base_url,
                product_type=category,
                confidence_score=0.9  # High confidence for JSON-LD
            )
            
        except Exception as e:
            logger.debug(f"Failed to create product from JSON-LD: {e}")
            return None
    
    def _extract_from_microdata(self, soup: BeautifulSoup, base_url: str = "") -> List[Product]:
        """Extract products from microdata/RDFa markup"""
        products = []
        
        # Find elements with Product itemtype
        product_elements = soup.find_all(attrs={'itemtype': re.compile(r'.*schema\.org/Product.*')})
        
        for element in product_elements:
            try:
                product = self._create_product_from_microdata(element, base_url)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Failed to extract product from microdata: {e}")
                continue
        
        return products
    
    def _create_product_from_microdata(self, element: Tag, base_url: str = "") -> Optional[Product]:
        """Create Product from microdata element"""
        try:
            # Extract title
            title_elem = element.find(attrs={'itemprop': 'name'})
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract price
            price, currency = None, None
            price_elem = element.find(attrs={'itemprop': re.compile(r'price|lowPrice')})
            if price_elem:
                price_text = price_elem.get('content') or price_elem.get_text(strip=True)
                if price_text:
                    price, currency = Product.parse_price_and_currency(price_text)
            
            # Extract brand
            brand = None
            brand_elem = element.find(attrs={'itemprop': 'brand'})
            if brand_elem:
                brand = brand_elem.get_text(strip=True)
            
            # Extract image
            image_url = None
            image_elem = element.find(attrs={'itemprop': 'image'})
            if image_elem:
                image_url = image_elem.get('src') or image_elem.get('content')
            
            # Extract URL
            product_url = None
            url_elem = element.find('a', href=True)
            if url_elem:
                product_url = url_elem.get('href')
            
            # Extract SKU
            sku = None
            sku_elem = element.find(attrs={'itemprop': re.compile(r'sku|mpn|gtin')})
            if sku_elem:
                sku = sku_elem.get('content') or sku_elem.get_text(strip=True)
            
            return self.create_product_from_data(
                title=title,
                price=price,
                currency=currency,
                vendor=brand,
                sku=sku,
                image_url=image_url,
                product_url=product_url,
                base_url=base_url,
                confidence_score=0.7  # Medium confidence for microdata
            )
            
        except Exception as e:
            logger.debug(f"Failed to create product from microdata: {e}")
            return None
    
    def _extract_from_css_heuristics(self, soup: BeautifulSoup, base_url: str = "") -> List[Product]:
        """Extract products using CSS heuristics as fallback"""
        products = []
        
        # Find product containers
        for selector in self.PRODUCT_CONTAINER_SELECTORS:
            containers = soup.select(selector)
            
            for container in containers:
                try:
                    product = self._create_product_from_container(container, base_url)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Failed to extract product from container: {e}")
                    continue
        
        return products
    
    def _create_product_from_container(self, container: Tag, base_url: str = "") -> Optional[Product]:
        """Create Product from HTML container using heuristics"""
        try:
            # Extract title
            title = self._extract_text_from_selectors(container, self.TITLE_SELECTORS)
            
            # Extract price
            price_text = self._extract_text_from_selectors(container, self.PRICE_SELECTORS)
            price, currency = self._parse_price_text(price_text)
            
            # Extract brand
            brand = self._extract_text_from_selectors(container, self.BRAND_SELECTORS)
            
            # Extract image
            image_url = self._extract_image_url(container)
            
            # Extract product URL
            product_url = self._extract_product_url(container)
            
            # Extract product ID
            product_id = (
                container.get('data-product-id') or
                container.get('data-id') or
                self.extract_product_id_from_url(product_url)
            )
            
            # Calculate confidence score based on available data
            confidence = self._calculate_confidence(title, price, image_url, product_url)
            
            # Only return products with reasonable confidence
            if confidence < 0.3:
                return None
            
            return self.create_product_from_data(
                title=title,
                price=price,
                currency=currency,
                vendor=brand,
                image_url=image_url,
                product_id=product_id,
                product_url=product_url,
                base_url=base_url,
                confidence_score=confidence
            )
            
        except Exception as e:
            logger.debug(f"Failed to create product from container: {e}")
            return None
    
    def _extract_text_from_selectors(self, container: Tag, selectors: List[str]) -> Optional[str]:
        """Extract text content using a list of CSS selectors"""
        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _extract_image_url(self, container: Tag) -> Optional[str]:
        """Extract image URL from container"""
        for selector in self.IMAGE_SELECTORS:
            img = container.select_one(selector)
            if img:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    return src
        return None
    
    def _extract_product_url(self, container: Tag) -> Optional[str]:
        """Extract product URL from container"""
        # Look for links within the container
        links = container.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if href and ('/product' in href or '/item' in href or '/p/' in href):
                return href
        
        # Fallback: return first link
        if links:
            return links[0].get('href')
        
        return None
    
    def _parse_price_text(self, price_text: str) -> Tuple[Optional[float], Optional[str]]:
        """Parse price text to extract amount and currency"""
        if not price_text:
            return None, None
        
        try:
            return Product.parse_price_and_currency(price_text)
        except:
            return None, None
    
    def _calculate_confidence(self, title: str, price: float, image_url: str, product_url: str) -> float:
        """Calculate confidence score for extracted product"""
        score = 0.0
        
        if title:
            score += 0.4
        if price is not None:
            score += 0.3
        if image_url:
            score += 0.2
        if product_url:
            score += 0.1
        
        return min(score, 1.0)
    
    def _deduplicate_and_rank(self, products: List[Product]) -> List[Product]:
        """Remove duplicates and sort by confidence score"""
        seen = set()
        unique_products = []
        
        # Sort by confidence score (highest first)
        products.sort(key=lambda p: getattr(p, 'confidence_score', 0.5), reverse=True)
        
        for product in products:
            # Create deduplication key
            key = (
                product.product_id or 
                product.product_name or 
                (product.product_url and product.product_url.split('?')[0])  # Remove query params
            )
            
            if key and key not in seen:
                seen.add(key)
                unique_products.append(product)
        
        return unique_products
