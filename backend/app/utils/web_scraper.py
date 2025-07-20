"""
Web Scraper Service
Simple web scraping to complement Exa.ai search results
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import time
import random


class WebScraper:
    """Simple web scraper for e-commerce sites"""
    
    def __init__(self):
        self.session = requests.Session()
        # Rotate user agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get randomized headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def scrape_url(self, url: str, delay: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Scrape a single URL and extract product information
        
        Args:
            url: URL to scrape
            delay: Delay between requests to be respectful
            
        Returns:
            Dictionary with scraped content or None if failed
        """
        try:
            # Add delay to be respectful
            time.sleep(delay)
            
            # Make request with random headers
            headers = self.get_random_headers()
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            result = {
                'url': url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'price': self._extract_price(soup, response.text),
                'images': self._extract_images(soup, url),
                'availability': self._extract_availability(soup, response.text),
                'brand': self._extract_brand(soup, response.text),
                'store_name': self._extract_store_name(url, soup),
                'product_name': self._extract_product_name(soup),
                'raw_text': soup.get_text(separator=' ', strip=True)[:2000]  # First 2000 chars
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            print(f"Scraping error for {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            return desc_tag.get('content', '')
        
        # Fallback to Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            return og_desc.get('content', '')
        
        return ""
    
    def _extract_price(self, soup: BeautifulSoup, raw_html: str) -> str:
        """Extract price using multiple strategies"""
        # Strategy 1: Look for common price selectors
        price_selectors = [
            '.price', '.price-current', '.price-now', '.current-price',
            '[data-price]', '.product-price', '.sale-price', '.offer-price',
            '.price-display', '.price-value', '.amount', '.cost'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                if self._is_valid_price(price_text):
                    return price_text
        
        # Strategy 2: Look for price in JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    offer = data['offers']
                    if isinstance(offer, list):
                        offer = offer[0]
                    if 'price' in offer:
                        return f"${offer['price']}"
            except:
                continue
        
        # Strategy 3: Regex search in raw HTML
        price_patterns = [
            r'\$\d+\.?\d*',
            r'£\d+\.?\d*',
            r'€\d+\.?\d*',
            r'(\d+\.?\d*)\s*(USD|CAD|GBP|EUR)',
            r'Price[:\s]*\$?\d+\.?\d*'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, raw_html, re.IGNORECASE)
            if matches:
                return matches[0] if isinstance(matches[0], str) else f"${matches[0][0]}"
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product images"""
        images = []
        
        # Strategy 1: Look for common image selectors
        img_selectors = [
            '.product-image img', '.product-photo img', '.main-image img',
            '[data-product-image]', '.gallery img', '.hero-image img'
        ]
        
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    # Convert relative URLs to absolute
                    full_url = urljoin(base_url, src)
                    if self._is_valid_image_url(full_url):
                        images.append(full_url)
        
        # Strategy 2: Look for Open Graph image
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        if og_image:
            src = og_image.get('content')
            if src:
                full_url = urljoin(base_url, src)
                if self._is_valid_image_url(full_url):
                    images.append(full_url)
        
        # Remove duplicates and return first 3
        return list(dict.fromkeys(images))[:3]
    
    def _extract_availability(self, soup: BeautifulSoup, raw_html: str) -> str:
        """Extract availability status"""
        availability_indicators = {
            'in stock': ['in stock', 'available', 'add to cart', 'buy now'],
            'out of stock': ['out of stock', 'sold out', 'unavailable', 'temporarily unavailable'],
            'limited': ['limited stock', 'only.*left', 'few remaining']
        }
        
        text_content = soup.get_text().lower()
        
        for status, indicators in availability_indicators.items():
            for indicator in indicators:
                if re.search(indicator, text_content):
                    return status
        
        return "unknown"
    
    def _extract_brand(self, soup: BeautifulSoup, raw_html: str) -> str:
        """Extract brand name"""
        # Look for brand in structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and 'brand' in data:
                    brand = data['brand']
                    if isinstance(brand, dict):
                        return brand.get('name', '')
                    return str(brand)
            except:
                continue
        
        # Look for brand in meta tags
        brand_meta = soup.find('meta', attrs={'name': 'brand'})
        if brand_meta:
            return brand_meta.get('content', '')
        
        # Look for brand in common selectors
        brand_selectors = ['.brand', '.brand-name', '[data-brand]']
        for selector in brand_selectors:
            brand_elem = soup.select_one(selector)
            if brand_elem:
                return brand_elem.get_text(strip=True)
        
        return ""
    
    def _extract_store_name(self, url: str, soup: BeautifulSoup) -> str:
        """Extract store name from URL or page"""
        # Extract from domain
        domain = urlparse(url).netloc.lower()
        
        # Common store mappings
        store_mappings = {
            'amazon.com': 'Amazon',
            'amazon.co.uk': 'Amazon UK',
            'amazon.ca': 'Amazon Canada',
            'ebay.com': 'eBay',
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
        
        # Fallback: Extract from site name or title
        site_name = soup.find('meta', attrs={'property': 'og:site_name'})
        if site_name:
            return site_name.get('content', '')
        
        # Extract from domain
        clean_domain = domain.replace('www.', '').split('.')[0]
        return clean_domain.title()
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name"""
        # Strategy 1: Look for h1 tags (often contain product names)
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text(strip=True)
            if text and len(text) > 5:  # Avoid very short titles
                return text
        
        # Strategy 2: Look for product-specific selectors
        product_selectors = [
            '.product-title', '.product-name', '[data-product-title]',
            '.item-title', '.listing-title'
        ]
        
        for selector in product_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text:
                    return text
        
        # Strategy 3: Use page title as fallback
        title = self._extract_title(soup)
        if title:
            # Clean up title (remove site name, etc.)
            title_parts = title.split(' - ')
            if len(title_parts) > 1:
                return title_parts[0].strip()
            return title
        
        return ""
    
    def _is_valid_price(self, price_text: str) -> bool:
        """Check if extracted text looks like a valid price"""
        if not price_text:
            return False
        
        # Look for currency symbols and numbers
        price_pattern = r'[\$£€¥]\s*\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*(?:USD|CAD|GBP|EUR|USD)'
        return bool(re.search(price_pattern, price_text))
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL looks like a valid image"""
        if not url:
            return False
        
        # Check for image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        url_lower = url.lower()
        
        # Either has image extension or contains image-related keywords
        has_extension = any(ext in url_lower for ext in image_extensions)
        has_image_keywords = any(keyword in url_lower for keyword in ['image', 'img', 'photo', 'picture'])
        
        return has_extension or has_image_keywords


def scrape_urls(urls: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
    """
    Convenience function to scrape multiple URLs
    
    Args:
        urls: List of URLs to scrape
        delay: Delay between requests
        
    Returns:
        List of scraped results
    """
    scraper = WebScraper()
    results = []
    
    for url in urls:
        result = scraper.scrape_url(url, delay)
        if result:
            results.append(result)
    
    return results 