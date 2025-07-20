"""
Jina AI Reader Service
Clean web content extraction using Jina AI's reader API
"""

import os
import requests
from typing import List, Dict, Any, Optional
import time
import concurrent.futures


class JinaReaderService:
    """Service for extracting clean content from URLs using Jina AI Reader"""
    
    def __init__(self, api_key: str = None):
        self.base_url = "https://r.jina.ai"
        self.api_key = api_key or os.getenv('JINA_API_KEY')
        self.session = requests.Session()
        
        # Set headers for better reliability
        headers = {
            'User-Agent': 'moleAI-shopping-assistant/1.0',
            'Accept': 'text/plain, application/json',
        }
        
        # Add API key if available for premium features
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            print(f"✅ Jina AI: Using API key for premium access")
        else:
            print("⚠️ Jina AI: Using free tier (rate limited)")
            
        self.session.headers.update(headers)
    
    def read_url(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Extract clean content from a single URL using Jina AI Reader
        
        Args:
            url: URL to extract content from
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with extracted content or None if failed
        """
        try:
            # Jina AI Reader endpoint
            jina_url = f"{self.base_url}/{url}"
            
            # Make request to Jina AI
            response = self.session.get(jina_url, timeout=timeout)
            response.raise_for_status()
            
            # Get the clean content
            clean_content = response.text
            
            # Parse and structure the response
            result = {
                'url': url,
                'content': clean_content,
                'content_length': len(clean_content),
                'success': True,
                'source': 'jina_reader'
            }
            
            # Try to extract structured information from the clean content
            structured_info = self._extract_product_info_from_content(clean_content, url)
            result.update(structured_info)
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Jina Reader error for {url}: {e}")
            return {
                'url': url,
                'content': '',
                'success': False,
                'error': str(e),
                'source': 'jina_reader'
            }
        except Exception as e:
            print(f"Unexpected error reading {url}: {e}")
            return {
                'url': url,
                'content': '',
                'success': False,
                'error': str(e),
                'source': 'jina_reader'
            }
    
    def read_urls_parallel(self, urls: List[str], max_workers: int = 5, delay: float = 0.2) -> List[Dict[str, Any]]:
        """
        Extract content from multiple URLs in parallel
        
        Args:
            urls: List of URLs to process
            max_workers: Maximum number of parallel workers
            delay: Delay between requests (for rate limiting)
            
        Returns:
            List of extraction results
        """
        results = []
        
        def read_with_delay(url: str) -> Dict[str, Any]:
            """Helper function to add delay between requests"""
            time.sleep(delay)
            return self.read_url(url)
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(read_with_delay, url): url for url in urls}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                if result:
                    results.append(result)
        
        return results
    
    def _extract_product_info_from_content(self, content: str, url: str) -> Dict[str, Any]:
        """
        Extract structured product information from clean content
        
        Args:
            content: Clean content from Jina Reader
            url: Original URL for context
            
        Returns:
            Dictionary with extracted product information
        """
        import re
        from urllib.parse import urlparse
        
        # Initialize result
        product_info = {
            'product_name': '',
            'price': '',
            'description': '',
            'brand': '',
            'availability': 'unknown',
            'store_name': self._extract_store_name_from_url(url),
            'images': []
        }
        
        if not content:
            return product_info
        
        # Split content into lines for easier processing
        lines = content.split('\n')
        content_lower = content.lower()
        
        # Extract product name (usually in title or first heading)
        product_info['product_name'] = self._extract_product_name(lines)
        
        # Extract price
        product_info['price'] = self._extract_price_from_content(content)
        
        # Extract description (look for longer text blocks)
        product_info['description'] = self._extract_description(lines)
        
        # Extract brand
        product_info['brand'] = self._extract_brand_from_content(content)
        
        # Extract availability
        product_info['availability'] = self._extract_availability_from_content(content_lower)
        
        # Extract image URLs from content
        product_info['images'] = self._extract_image_urls_from_content(content)
        
        return product_info
    
    def _extract_product_name(self, lines: List[str]) -> str:
        """Extract product name from content lines"""
        # Look for title-like lines (usually first few non-empty lines)
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                # Skip lines that look like navigation or metadata
                skip_patterns = ['home', 'menu', 'cart', 'sign in', 'search', 'categories']
                if not any(pattern in line.lower() for pattern in skip_patterns):
                    return line
        
        return ""
    
    def _extract_price_from_content(self, content: str) -> str:
        """Extract price from content using regex patterns"""
        import re
        
        # Common price patterns
        price_patterns = [
            r'\$\d+\.?\d*',  # $29.99, $29
            r'£\d+\.?\d*',   # £29.99
            r'€\d+\.?\d*',   # €29.99
            r'¥\d+\.?\d*',   # ¥2999
            r'\d+\.\d{2}\s*(?:USD|CAD|GBP|EUR)',  # 29.99 USD
            r'Price[:\s]*\$?\d+\.?\d*',  # Price: $29.99
            r'Sale[:\s]*\$?\d+\.?\d*',   # Sale: $29.99
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return ""
    
    def _extract_description(self, lines: List[str]) -> str:
        """Extract product description from content lines"""
        # Look for longer text blocks that aren't titles
        description_candidates = []
        
        for line in lines:
            line = line.strip()
            # Look for substantial text blocks
            if 50 <= len(line) <= 500:  # Good description length
                # Skip obvious non-description content
                skip_patterns = ['cookie', 'privacy', 'terms', 'shipping', 'return']
                if not any(pattern in line.lower() for pattern in skip_patterns):
                    description_candidates.append(line)
        
        # Return the first good candidate or first few lines
        if description_candidates:
            return description_candidates[0]
        
        # Fallback: combine first few substantial lines
        substantial_lines = [line.strip() for line in lines if 20 <= len(line.strip()) <= 200]
        if substantial_lines:
            return ' '.join(substantial_lines[:2])
        
        return ""
    
    def _extract_brand_from_content(self, content: str) -> str:
        """Extract brand name from content"""
        import re
        
        # Look for brand patterns
        brand_patterns = [
            r'Brand[:\s]+([A-Za-z][A-Za-z\s&]+)',
            r'by ([A-Z][a-z]+)',
            r'from ([A-Z][a-z]+)',
        ]
        
        for pattern in brand_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                brand = matches[0].strip()
                if len(brand) <= 30:  # Reasonable brand name length
                    return brand
        
        return ""
    
    def _extract_availability_from_content(self, content_lower: str) -> str:
        """Extract availability status from content"""
        if any(phrase in content_lower for phrase in ['in stock', 'available now', 'add to cart', 'buy now']):
            return 'in stock'
        elif any(phrase in content_lower for phrase in ['out of stock', 'sold out', 'unavailable']):
            return 'out of stock'
        elif any(phrase in content_lower for phrase in ['limited stock', 'only', 'left']):
            return 'limited'
        else:
            return 'unknown'
    
    def _extract_image_urls_from_content(self, content: str) -> List[str]:
        """Extract image URLs from content"""
        import re
        
        # Look for image URLs in the content
        image_patterns = [
            r'https?://[^\s]+\.(?:jpg|jpeg|png|webp|gif)',
            r'https?://[^\s]+/images/[^\s]+',
        ]
        
        images = []
        for pattern in image_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            images.extend(matches)
        
        # Remove duplicates and return first 3
        return list(dict.fromkeys(images))[:3]
    
    def _extract_store_name_from_url(self, url: str) -> str:
        """Extract store name from URL"""
        from urllib.parse import urlparse
        
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
            'wayfair.com': 'Wayfair',
            'newegg.com': 'Newegg',
            'costco.com': 'Costco'
        }
        
        for domain_key, store_name in store_mappings.items():
            if domain_key in domain:
                return store_name
        
        # Fallback: clean domain name
        clean_domain = domain.replace('www.', '').split('.')[0]
        return clean_domain.title()


# Convenience functions
def read_urls_with_jina(urls: List[str], max_workers: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to read multiple URLs with Jina AI Reader
    
    Args:
        urls: List of URLs to read
        max_workers: Maximum parallel workers
        
    Returns:
        List of extracted content
    """
    service = JinaReaderService()
    return service.read_urls_parallel(urls, max_workers)


def read_url_with_jina(url: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to read a single URL with Jina AI Reader
    
    Args:
        url: URL to read
        
    Returns:
        Extracted content or None
    """
    service = JinaReaderService()
    return service.read_url(url) 