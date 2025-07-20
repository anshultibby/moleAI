"""
Hybrid Search Service
Combines Exa.ai high-quality search with Jina AI Reader for complete product information
"""

import os
from typing import List, Dict, Any, Optional
from .exa_service import ExaService, ExaSearchResult
from .jina_service import JinaReaderService
import concurrent.futures
import time


class HybridSearchService:
    """Service that combines Exa search with Jina AI Reader"""
    
    def __init__(self, exa_api_key: str = None, jina_api_key: str = None):
        self.exa_service = ExaService(exa_api_key)
        self.jina_service = JinaReaderService(jina_api_key)
    
    def search_products(
        self,
        query: str,
        num_results: int = 10,
        max_price: Optional[float] = None,
        specific_stores: Optional[List[str]] = None,
        extract_content: bool = True,
        max_extract_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for products using Exa, then extract content using Jina AI Reader
        
        Args:
            query: Product search query
            num_results: Number of search results to get from Exa
            max_price: Maximum price filter
            specific_stores: List of specific store domains to search
            extract_content: Whether to extract content from search results for detailed info
            max_extract_results: Maximum number of results to extract content from (to save time)
        
        Returns:
            List of enriched product information
        """
        import time
        hybrid_start = time.time()
        
        print(f"Hybrid search for: {query}")
        print(f"🕐 TIMING: Hybrid search started at {time.strftime('%H:%M:%S')}")
        
        # Step 1: Get search results from Exa
        step1_start = time.time()
        print(f"Step 1: Searching with Exa.ai...")
        if specific_stores:
            exa_results = self.exa_service.search_specific_stores(
                query, specific_stores, num_results
            )
        else:
            # Search the entire web for shopping results - no domain restrictions!
            search_query = f"{query} buy online store price"
            if max_price:
                search_query += f" under ${max_price}"
            
            exa_results = self.exa_service.search(
                query=search_query,
                num_results=num_results,
                type="neural",
                include_text=True,
                text_type="text"
            )
        
        step1_end = time.time()
        print(f"Found {len(exa_results)} search results from Exa")
        print(f"🕐 TIMING: Exa search took {step1_end - step1_start:.2f}s")
        
        if not exa_results:
            return []
        
        # Step 2: Optionally extract content from results for detailed product information
        if extract_content:
            step2_start = time.time()
            print(f"Step 2: Extracting content from top {min(len(exa_results), max_extract_results)} results...")
            
            # Limit content extraction to save time and be respectful
            urls_to_extract = [result.url for result in exa_results[:max_extract_results]]
            
            # Extract content in parallel using Jina AI Reader
            extracted_data = self._extract_content_parallel(urls_to_extract, max_workers=3)
            step2_end = time.time()
            print(f"🕐 TIMING: Content extraction took {step2_end - step2_start:.2f}s")
            
            # Step 3: Combine Exa data with extracted content
            step3_start = time.time()
            enriched_results = self._combine_exa_and_extracted_data(exa_results, extracted_data)
            step3_end = time.time()
            print(f"🕐 TIMING: Data combination took {step3_end - step3_start:.2f}s")
            
            hybrid_end = time.time()
            print(f"🕐 TIMING: Total hybrid search took {hybrid_end - hybrid_start:.2f}s")
            print(f"Successfully enriched {len(enriched_results)} results")
            return enriched_results
        else:
            # Return just Exa data if content extraction is disabled
            hybrid_end = time.time()
            print(f"🕐 TIMING: Total hybrid search (no extraction) took {hybrid_end - hybrid_start:.2f}s")
            return self._convert_exa_results_to_products(exa_results)
    
    def _extract_content_parallel(self, urls: List[str], max_workers: int = 3) -> Dict[str, Dict[str, Any]]:
        """Extract content from URLs in parallel using Jina AI Reader"""
        extracted_data = {}
        
        # Use Jina's parallel processing
        results = self.jina_service.read_urls_parallel(urls, max_workers=max_workers, delay=0.2)
        
        # Convert to dictionary indexed by URL
        for result in results:
            if result and result.get('success'):
                extracted_data[result['url']] = result
        
        return extracted_data
    
    def _combine_exa_and_extracted_data(
        self, 
        exa_results: List[ExaSearchResult], 
        extracted_data: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine Exa search results with Jina AI extracted content"""
        enriched_results = []
        
        for exa_result in exa_results:
            # Start with Exa data
            product = {
                'url': exa_result.url,
                'title': exa_result.title,
                'search_score': exa_result.score,
                'published_date': exa_result.published_date,
                'source': 'exa+scraper'
            }
            
            # Add Exa text content
            if exa_result.text:
                product['exa_content'] = exa_result.text
            
            if exa_result.highlights:
                product['highlights'] = exa_result.highlights
            
            # Enhance with extracted content if available
            extracted = extracted_data.get(exa_result.url)
            if extracted:
                # Prioritize extracted data for product-specific fields
                product.update({
                    'product_name': extracted.get('product_name') or self._extract_product_name_from_title(exa_result.title),
                    'price': extracted.get('price', ''),
                    'store_name': extracted.get('store_name', ''),
                    'description': extracted.get('description', ''),
                    'images': extracted.get('images', []),
                    'availability': extracted.get('availability', 'unknown'),
                    'brand': extracted.get('brand', ''),
                    'extracted_content': extracted.get('content', ''),
                    'content_length': extracted.get('content_length', 0)
                })
                
                # Use best available image
                if extracted.get('images'):
                    product['image_url'] = extracted['images'][0]
                else:
                    product['image_url'] = ''
            else:
                # Fallback to Exa data only
                product.update({
                    'product_name': self._extract_product_name_from_title(exa_result.title),
                    'price': self._extract_price_from_exa_content(exa_result.text),
                    'store_name': self._extract_store_from_url(exa_result.url),
                    'description': exa_result.text[:200] if exa_result.text else '',
                    'images': [],
                    'image_url': '',
                    'availability': 'unknown',
                    'brand': ''
                })
            
            enriched_results.append(product)
        
        return enriched_results
    
    def _convert_exa_results_to_products(self, exa_results: List[ExaSearchResult]) -> List[Dict[str, Any]]:
        """Convert Exa results to product format without additional scraping"""
        products = []
        
        for result in exa_results:
            product = {
                'url': result.url,
                'title': result.title,
                'product_name': self._extract_product_name_from_title(result.title),
                'price': self._extract_price_from_exa_content(result.text),
                'store_name': self._extract_store_from_url(result.url),
                'description': result.text[:200] if result.text else '',
                'images': [],
                'image_url': '',
                'availability': 'unknown',
                'brand': '',
                'search_score': result.score,
                'source': 'exa_only'
            }
            products.append(product)
        
        return products
    
    def _extract_product_name_from_title(self, title: str) -> str:
        """Extract a clean product name from the page title"""
        if not title:
            return "Product"
        
        # Clean up common patterns in titles
        title = title.replace(' - Amazon.com', '')
        title = title.replace(' | Target', '')
        title = title.replace(' - Walmart.com', '')
        title = title.replace(' | Best Buy', '')
        
        # Split on common separators and take the first meaningful part
        separators = [' - ', ' | ', ' : ', ' :: ']
        for sep in separators:
            if sep in title:
                parts = title.split(sep)
                if parts[0].strip():
                    return parts[0].strip()
        
        # If no separators, return the whole title (up to 100 chars)
        return title[:100].strip()
    
    def _extract_price_from_exa_content(self, content: str) -> str:
        """Try to extract price from Exa content"""
        if not content:
            return ""
        
        import re
        # Look for price patterns in the content
        price_patterns = [
            r'\$\d+\.?\d*',
            r'£\d+\.?\d*',
            r'€\d+\.?\d*',
            r'Price[:\s]*\$?\d+\.?\d*'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content)
            if matches:
                return matches[0]
        
        return ""
    
    def _extract_store_from_url(self, url: str) -> str:
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
            'wayfair.com': 'Wayfair'
        }
        
        for domain_key, store_name in store_mappings.items():
            if domain_key in domain:
                return store_name
        
        # Fallback: clean domain name
        clean_domain = domain.replace('www.', '').split('.')[0]
        return clean_domain.title()


# Convenience functions
def search_products_hybrid(
    query: str,
    exa_api_key: str = None,
    jina_api_key: str = None,
    num_results: int = 10,
    max_price: Optional[float] = None,
    specific_stores: Optional[List[str]] = None,
    extract_content: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function for hybrid product search
    
    Args:
        query: Product search query
        exa_api_key: Exa API key (optional, will use env var if not provided)
        jina_api_key: Jina API key (optional, will use env var if not provided)
        num_results: Number of results to get
        max_price: Maximum price filter
        specific_stores: List of specific store domains
        extract_content: Whether to extract content for detailed product info
    
    Returns:
        List of enriched product data
    """
    service = HybridSearchService(exa_api_key, jina_api_key)
    return service.search_products(
        query=query,
        num_results=num_results,
        max_price=max_price,
        specific_stores=specific_stores,
        extract_content=extract_content
    ) 