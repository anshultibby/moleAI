"""
Shopify JSON Service
Direct JSON API access to Shopify stores for ultra-fast product discovery
"""

import requests
import json
from typing import List, Dict, Any, Optional, Tuple
import re
import time
from urllib.parse import urljoin, urlparse

# Import progress streaming function
from .gemini_tools_converter import stream_progress_update

from .shopify import ShopifyProductConverter, LLMProductFilter
from .debug_tracker import get_debug_tracker


class ShopifyJSONService:
    """Simplified main service for searching Shopify stores via JSON endpoints"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Initialize organized modules
        self.converter = ShopifyProductConverter()
        self.llm_filter = LLMProductFilter()
    
    def search_store_products(self, store_domain: str, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search a single Shopify store for products matching the query
        
        Args:
            store_domain: Shopify domain (e.g., 'store.myshopify.com')
            query: Search query (e.g., 'black leggings')
            limit: Maximum products to return
            
        Returns:
            List of relevant products
        """
        if not store_domain or not query.strip():
            return []
        
        # Validate domain first (quick check)
        if not self._is_valid_domain(store_domain):
            print(f"   ❌ Invalid domain: {store_domain}")
            return []
            
        try:
            # Get debug tracker for this session
            debug_tracker = get_debug_tracker()
            if debug_tracker:
                debug_tracker.start_timing_phase(f"shopify_search_{store_domain}")
            
            # Step 1: Extract products - FASTER with progress
            print(f"   📄 Fetching products from {store_domain}...")
            raw_products, working_base_url = self._extract_all_available_products(store_domain, limit * 6)  # Reduced multiplier for speed
            
            if not raw_products:
                print(f"   ❌ No products found")
                if debug_tracker:
                    debug_tracker.track_error(f"No raw products found for {store_domain}", "shopify_fetch")
                return []
            
            print(f"   📦 Got {len(raw_products)} raw products, converting...")
            
            # Step 2: Convert to LLM-friendly format
            llm_readable_products = self.converter.convert_to_llm_format(raw_products, working_base_url)
            
            print(f"   🔧 Converted to {len(llm_readable_products)} available products, filtering...")
            
            # Step 3: Use LLM to filter for relevance  
            relevant_products = self.llm_filter.filter_products(llm_readable_products, query)
            
            final_results = relevant_products[:limit]
            print(f"   ✅ Final: {len(final_results)} relevant products")
            
            # Track debug data
            if debug_tracker:
                debug_tracker.track_shopify_json(raw_products, llm_readable_products, final_results)
                debug_tracker.end_timing_phase(f"shopify_search_{store_domain}")
                debug_tracker.track_search_results(f"shopify_{store_domain}", len(final_results), 0)  # Timing handled separately
            
            return final_results
            
        except Exception as e:
            print(f"   ❌ Error searching {store_domain}: {e}")
            return []

    def _extract_all_available_products(self, store_domain: str, max_products: int) -> Tuple[List[Dict], str]:
        """Extract raw product data from Shopify store - no filtering, just extraction"""
        clean_domain = self._clean_domain(store_domain)
        all_products = []
        working_base_url = ""
        
        # Try multiple URL patterns
        for base_url in self._get_url_variants(clean_domain):
            try:
                store_products = self._fetch_raw_products_from_url(base_url, max_products)
                if store_products:  # If we got results, save the working URL
                    all_products.extend(store_products)
                    working_base_url = base_url
                    break
            except Exception:
                continue  # Try next URL variant
        
        return all_products, working_base_url

    def _fetch_raw_products_from_url(self, base_url: str, max_products: int) -> List[Dict]:
        """Fetch raw products from a specific Shopify URL"""
        all_products = []
        page = 1
        
        while len(all_products) < max_products and page <= 3:  # Limit to 3 pages for speed
            products_url = f"{base_url}/products.json"
            params = {'limit': min(250, max_products - len(all_products)), 'page': page}
            
            # Only show page info if fetching multiple pages
            if page == 1:
                print(f"     📄 Fetching products...")
            else:
                print(f"     📄 Page {page}...")
            
            try:
                response = self.session.get(products_url, params=params, timeout=8)  # Reasonable timeout
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get('products', [])
                    
                    if not products:  # No more products
                        break
                    
                    all_products.extend(products)
                    
                    # Show progress
                    if len(products) > 0:
                        print(f"     ✅ Got {len(products)} products (total: {len(all_products)})")
                    
                    page += 1
                    
                    # Quick rate limiting
                    time.sleep(0.05)  # Very fast
                    
                else:
                    print(f"     ❌ HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"     ❌ Error: {str(e)[:50]}...")
                break
        
        return all_products

    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize domain"""
        domain = domain.lower().strip()
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.rstrip('/')
        return domain
    
    def _get_url_variants(self, domain: str) -> List[str]:
        """Generate possible Shopify URL variants"""
        variants = []
        
        # Direct domain
        if not domain.endswith('.myshopify.com'):
            variants.append(f"https://{domain}")
        
        # MyShopify subdomain
        if '.myshopify.com' in domain:
            variants.append(f"https://{domain}")
        else:
            # Extract store name and try myshopify.com
            store_name = domain.split('.')[0]
            variants.append(f"https://{store_name}.myshopify.com")
        
        return variants

    def _is_valid_domain(self, domain: str) -> bool:
        """Check if domain is valid for Shopify search (not localhost, not fake domains)"""
        if not domain:
            return False
        
        domain = domain.lower().strip()
        
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.rstrip('/')
        
        # Filter out localhost and development domains
        localhost_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            'localhost:',  # Catches localhost:3000, localhost:8080, etc.
        ]
        
        for pattern in localhost_patterns:
            if pattern in domain:
                print(f"   🚫 Filtering out localhost domain: {domain}")
                return False
        
        # Filter out fake/test domains
        fake_domains = [
            'example.com',
            'test.com',
            'sample.com',
            'demo.com',
            'fake.com'
        ]
        
        for fake in fake_domains:
            if fake in domain:
                print(f"   🚫 Filtering out fake domain: {domain}")
                return False
        
        # Must have at least one dot for valid domain
        if '.' not in domain:
            return False
        
        return True


def search_multiple_stores(store_domains: List[str], query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Search multiple Shopify stores and return aggregated results
    
    Args:
        store_domains: List of Shopify domains
        query: Search query  
        max_results: Maximum total results to return
        
    Returns:
        Aggregated list of products from all stores
    """
    if not store_domains or not query.strip():
        return []
    
    print(f"🚀 Starting search for '{query}' across {len(store_domains)} stores...")
    
    # Validate domains first - FASTER with progress
    print(f"⚡ Step 1/3: Validating store accessibility...")
    valid_domains = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    # Show progress for domain validation
    for i, domain in enumerate(store_domains):
        if (i + 1) % 5 == 0 or i == 0:
            print(f"   📊 Checking domains: {i+1}/{len(store_domains)}, {len(valid_domains)} valid so far...")
            
        try:
            test_url = f"https://{domain}/products.json"
            response = session.head(test_url, timeout=3)  # Faster timeout
            if response.status_code in [200, 301, 302]:
                valid_domains.append(domain)
                stream_progress_update(f"   ✅ *{domain}* - accessible store")  # Stream validated stores in italics
            # Only print successful validations to reduce noise
        except Exception:
            pass  # Silent failure to reduce noise
    
    if not valid_domains:
        print("❌ No valid domains found")
        return []
    
    print(f"✅ {len(valid_domains)} stores are accessible")
    
    # Search each store - FASTER with progress
    print(f"⚡ Step 2/3: Searching products in {len(valid_domains)} stores...")
    all_products = []
    service = ShopifyJSONService()
    
    results_per_store = max(10, max_results // len(valid_domains)) if valid_domains else 20
    
    for i, domain in enumerate(valid_domains):
        store_url = f"https://{domain}"
        stream_progress_update(f"🏪 [{i+1}/{len(valid_domains)}] Searching *[{domain}]({store_url})*...")  # Clickable link in italics
        try:
            products = service.search_store_products(domain, query, results_per_store)
            all_products.extend(products)
            print(f"   ✅ Found {len(products)} products ({len(all_products)} total so far)")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Process results
    print(f"⚡ Step 3/3: Processing {len(all_products)} products...")
    
    # Remove duplicates and sort by relevance
    unique_products = []
    seen_urls = set()
    
    for product in all_products:
        url = product.get('product_url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_products.append(product)
    
    # Sort by relevance score (higher is better)
    unique_products.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    final_results = unique_products[:max_results]
    print(f"✅ Search complete: {len(final_results)} final results")
    
    return final_results 