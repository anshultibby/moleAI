"""
Scrapfly Service
Professional web scraping with anti-bot protection for e-commerce sites
"""

import os
import requests
from typing import List, Dict, Any, Optional
import time
import concurrent.futures
from urllib.parse import urlencode
import json


class ScrapflyService:
    """Service for professional web scraping using Scrapfly API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SCRAPFLY_API_KEY')
        if not self.api_key:
            raise ValueError("SCRAPFLY_API_KEY is required")
        
        self.base_url = "https://api.scrapfly.io/scrape"
        self.session = requests.Session()
    
    def scrape_url(
        self,
        url: str,
        render_js: bool = True,
        country: str = "US",
        asp: bool = True,  # Anti-scraping protection
        auto_scroll: bool = False,
        wait_for_selector: str = None,
        extract_selector: Dict[str, str] = None,
        timeout: int = 30000
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape a single URL using Scrapfly
        
        Args:
            url: URL to scrape
            render_js: Whether to render JavaScript
            country: Country for proxy (US, UK, CA, etc.)
            asp: Enable anti-scraping protection
            auto_scroll: Auto-scroll the page
            wait_for_selector: CSS selector to wait for
            extract_selector: Dict of CSS selectors to extract specific data
            timeout: Request timeout in milliseconds
            
        Returns:
            Dictionary with scraped content or None if failed
        """
        try:
            # Build Scrapfly parameters
            params = {
                'key': self.api_key,
                'url': url,
                'render_js': str(render_js).lower(),
                'country': country,
                'asp': str(asp).lower(),
                'timeout': timeout
            }
            
            if auto_scroll:
                params['auto_scroll'] = 'true'
            
            if wait_for_selector:
                params['wait_for_selector'] = wait_for_selector
            
            if extract_selector:
                # Scrapfly extraction rules
                extraction_rules = {}
                for key, selector in extract_selector.items():
                    extraction_rules[key] = {'selector': selector}
                params['extraction_rules'] = json.dumps(extraction_rules)
            
            # Make request to Scrapfly
            response = self.session.get(self.base_url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('result', {}).get('status_code') != 200:
                print(f"Scrapfly returned non-200 status: {data.get('result', {}).get('status_code')}")
                return None
            
            # Extract content
            result = {
                'url': url,
                'content': data.get('result', {}).get('content', ''),
                'status_code': data.get('result', {}).get('status_code'),
                'success': True,
                'source': 'scrapfly',
                'scraped_at': data.get('result', {}).get('scraped_at')
            }
            
            # Add extracted data if available
            if 'extraction' in data.get('result', {}):
                result['extracted_data'] = data['result']['extraction']
            
            # Extract product information from the content
            product_info = self._extract_product_info_from_content(result['content'], url)
            result.update(product_info)
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Scrapfly request error for {url}: {e}")
            return {
                'url': url,
                'content': '',
                'success': False,
                'error': str(e),
                'source': 'scrapfly'
            }
        except Exception as e:
            print(f"Scrapfly error for {url}: {e}")
            return {
                'url': url,
                'content': '',
                'success': False,
                'error': str(e),
                'source': 'scrapfly'
            }
    
    def scrape_product_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a product page with e-commerce optimizations
        
        Args:
            url: Product page URL
            
        Returns:
            Dictionary with product information
        """
        # E-commerce specific extraction selectors
        extract_selectors = {
            'title': 'h1, .product-title, .product-name, [data-testid="product-title"]',
            'price': '.price, .product-price, .current-price, [data-testid="price-current"]',
            'image': '.product-image img, .hero-image img, .main-image img',
            'description': '.product-description, .product-details, .product-summary',
            'availability': '.availability, .stock-status, .in-stock, .out-of-stock',
            'brand': '.brand, .brand-name, [data-brand]',
            'rating': '.rating, .stars, .review-score'
        }
        
        return self.scrape_url(
            url=url,
            render_js=True,
            asp=True,
            auto_scroll=False,
            wait_for_selector='.price, .product-title, h1',  # Wait for key product elements
            extract_selector=extract_selectors,
            timeout=45000  # Longer timeout for complex product pages
        )
    
    def scrape_urls_parallel(
        self,
        urls: List[str],
        max_workers: int = 3,
        delay: float = 1.0,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs in parallel
        
        Args:
            urls: List of URLs to scrape
            max_workers: Maximum parallel workers
            delay: Delay between requests
            **kwargs: Additional parameters for scrape_url
            
        Returns:
            List of scraping results
        """
        results = []
        
        def scrape_with_delay(url: str) -> Dict[str, Any]:
            """Helper function to add delay between requests"""
            time.sleep(delay)
            return self.scrape_product_page(url) if 'extract_selector' not in kwargs else self.scrape_url(url, **kwargs)
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(scrape_with_delay, url): url for url in urls}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                if result:
                    results.append(result)
        
        return results
    
    def _extract_product_info_from_content(self, content: str, url: str) -> Dict[str, Any]:
        """
        Extract structured product information from HTML content
        
        Args:
            content: HTML content from Scrapfly
            url: Original URL for context
            
        Returns:
            Dictionary with extracted product information
        """
        from bs4 import BeautifulSoup
        import re
        
        # Initialize result
        product_info = {
            'product_name': '',
            'price': '',
            'description': '',
            'brand': '',
            'availability': 'unknown',
            'store_name': self._extract_store_name_from_url(url),
            'images': [],
            'rating': ''
        }
        
        if not content:
            return product_info
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract product name
            product_info['product_name'] = self._extract_product_name(soup)
            
            # Extract price
            product_info['price'] = self._extract_price(soup)
            
            # Extract description
            product_info['description'] = self._extract_description(soup)
            
            # Extract brand
            product_info['brand'] = self._extract_brand(soup)
            
            # Extract availability
            product_info['availability'] = self._extract_availability(soup)
            
            # Extract images
            product_info['images'] = self._extract_images(soup, url)
            
            # Extract rating
            product_info['rating'] = self._extract_rating(soup)
            
        except Exception as e:
            print(f"Error extracting product info: {e}")
        
        return product_info
    
    def _extract_product_name(self, soup) -> str:
        """Extract product name from soup"""
        selectors = [
            'h1',
            '.product-title',
            '.product-name', 
            '[data-testid="product-title"]',
            '.pdp-product-name',
            '.item-title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    return text
        
        return ""
    
    def _extract_price(self, soup) -> str:
        """Extract price from soup"""
        selectors = [
            '.price',
            '.product-price',
            '.current-price',
            '[data-testid="price-current"]',
            '.sale-price',
            '.offer-price',
            '.price-current'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if self._is_valid_price(text):
                    return text
        
        # Fallback: regex search
        import re
        price_patterns = [r'\$\d+\.?\d*', r'£\d+\.?\d*', r'€\d+\.?\d*']
        text_content = soup.get_text()
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                return matches[0]
        
        return ""
    
    def _extract_description(self, soup) -> str:
        """Extract description from soup"""
        selectors = [
            '.product-description',
            '.product-details',
            '.product-summary',
            '.description',
            '.pdp-description'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 20:
                    return text[:500]  # Limit to 500 chars
        
        return ""
    
    def _extract_brand(self, soup) -> str:
        """Extract brand from soup"""
        selectors = [
            '.brand',
            '.brand-name',
            '[data-brand]',
            '.manufacturer'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) <= 50:
                    return text
        
        return ""
    
    def _extract_availability(self, soup) -> str:
        """Extract availability from soup"""
        text_content = soup.get_text().lower()
        
        if any(phrase in text_content for phrase in ['in stock', 'available', 'add to cart']):
            return 'in stock'
        elif any(phrase in text_content for phrase in ['out of stock', 'sold out', 'unavailable']):
            return 'out of stock'
        elif any(phrase in text_content for phrase in ['limited stock', 'only', 'left']):
            return 'limited'
        
        return 'unknown'
    
    def _extract_images(self, soup, base_url: str) -> List[str]:
        """Extract product images from soup"""
        from urllib.parse import urljoin
        
        selectors = [
            '.product-image img',
            '.hero-image img',
            '.main-image img',
            '.gallery img',
            '[data-testid="product-image"] img'
        ]
        
        images = []
        for selector in selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    full_url = urljoin(base_url, src)
                    if self._is_valid_image_url(full_url):
                        images.append(full_url)
        
        # Remove duplicates and return first 3
        return list(dict.fromkeys(images))[:3]
    
    def _extract_rating(self, soup) -> str:
        """Extract rating from soup"""
        selectors = [
            '.rating',
            '.stars',
            '.review-score',
            '[data-testid="rating"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        
        return ""
    
    def _is_valid_price(self, price_text: str) -> bool:
        """Check if text looks like a valid price"""
        import re
        if not price_text:
            return False
        
        price_pattern = r'[\$£€¥]\s*\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*(?:USD|CAD|GBP|EUR)'
        return bool(re.search(price_pattern, price_text))
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL looks like a valid image"""
        if not url:
            return False
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        url_lower = url.lower()
        
        has_extension = any(ext in url_lower for ext in image_extensions)
        has_image_keywords = any(keyword in url_lower for keyword in ['image', 'img', 'photo'])
        
        return has_extension or has_image_keywords
    
    def _extract_store_name_from_url(self, url: str) -> str:
        """Extract store name from URL"""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc.lower()
        
        store_mappings = {
            'amazon.com': 'Amazon',
            'amazon.co.uk': 'Amazon UK',
            'target.com': 'Target',
            'walmart.com': 'Walmart',
            'bestbuy.com': 'Best Buy',
            'homedepot.com': 'Home Depot',
            'lowes.com': "Lowe's",
            'macys.com': "Macy's",
            'nordstrom.com': 'Nordstrom',
            'zappos.com': 'Zappos',
            'etsy.com': 'Etsy',
            'wayfair.com': 'Wayfair'
        }
        
        for domain_key, store_name in store_mappings.items():
            if domain_key in domain:
                return store_name
        
        clean_domain = domain.replace('www.', '').split('.')[0]
        return clean_domain.title()


# Convenience functions
def scrape_product_with_scrapfly(url: str, api_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to scrape a single product page
    
    Args:
        url: Product page URL
        api_key: Scrapfly API key (optional, will use env var if not provided)
        
    Returns:
        Product information or None
    """
    service = ScrapflyService(api_key)
    return service.scrape_product_page(url)


def scrape_products_with_scrapfly(urls: List[str], api_key: str = None) -> List[Dict[str, Any]]:
    """
    Convenience function to scrape multiple product pages
    
    Args:
        urls: List of product page URLs
        api_key: Scrapfly API key (optional, will use env var if not provided)
        
    Returns:
        List of product information
    """
    service = ScrapflyService(api_key)
    return service.scrape_urls_parallel(urls, max_workers=3, delay=2.0) 