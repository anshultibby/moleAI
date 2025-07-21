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
from .progress_utils import stream_progress_update

from .shopify import ShopifyProductConverter, LLMProductFilter
from .debug_tracker import get_debug_tracker
from .funnel_visualizer import get_funnel_visualizer


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
    
    def search_store_products(self, store_domain: str, query: str, limit: int = 300, product_callback=None) -> List[Dict[str, Any]]:
        """
        Search a single Shopify store for products matching the query
        
        Args:
            store_domain: Shopify domain (e.g., 'store.myshopify.com')
            query: Search query (e.g., 'black leggings')
            limit: Maximum products to return (increased default for more variety)
            product_callback: Optional callback function to stream products as they're found
            
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
            # Get debug tracker and funnel visualizer for this session
            debug_tracker = get_debug_tracker()
            funnel_visualizer = get_funnel_visualizer()
            
            if debug_tracker:
                debug_tracker.start_timing_phase(f"shopify_search_{store_domain}")
            
            # Step 1: Extract products - FASTER with progress
            print(f"   📄 Fetching products from {store_domain}...")
            raw_products, working_base_url = self._extract_all_available_products(store_domain, limit * 10)  # INCREASED multiplier for more diversity
            
            # Track raw data in funnel
            if funnel_visualizer:
                try:
                    funnel_visualizer.track_raw_data(raw_products, store_domain)
                except Exception as e:
                    print(f"   ⚠️  Funnel tracking error: {e}")
            
            if not raw_products:
                print(f"   ❌ No products found")
                if debug_tracker:
                    debug_tracker.track_error(f"No raw products found for {store_domain}", "shopify_fetch")
                if funnel_visualizer:
                    funnel_visualizer.track_error(f"No raw products found for {store_domain}", "shopify_fetch")
                return []
            
            print(f"   📦 Got {len(raw_products)} raw products, converting...")
            
            # Step 2: Convert to LLM-friendly format (includes prefiltering)
            llm_readable_products = self.converter.convert_to_llm_format(raw_products, working_base_url)
            
            print(f"   🔧 Converted to {len(llm_readable_products)} available products, filtering...")
            
            # Step 3: Skip individual LLM filtering - do basic filtering only for streaming
            # We'll do batch LLM filtering later for better efficiency
            basic_filtered_products = self.llm_filter._basic_filter_by_query(llm_readable_products, query)
            
            # Return basic filtered products (LLM batch filtering happens later)
            print(f"   ✅ Basic filter: {len(basic_filtered_products)} products")
            
            # Stream products to frontend immediately if callback provided
            if product_callback and basic_filtered_products:
                try:
                    for product in basic_filtered_products:
                        product_callback(product)
                except Exception as e:
                    print(f"   ⚠️  Product streaming error: {e}")
            
            # Track final results in funnel
            if funnel_visualizer:
                try:
                    funnel_visualizer.track_final_results(basic_filtered_products)
                except Exception as e:
                    print(f"   ⚠️  Funnel tracking error: {e}")
            
            # Track debug data
            if debug_tracker:
                debug_tracker.track_shopify_json(raw_products, llm_readable_products, basic_filtered_products, store_domain)
                debug_tracker.end_timing_phase(f"shopify_search_{store_domain}")
                debug_tracker.track_search_results(f"shopify_{store_domain}", len(basic_filtered_products), 0)  # Timing handled separately
            
            return basic_filtered_products
            
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


def search_multiple_stores(store_domains: List[str], query: str, max_results: int = 300, product_callback=None, max_price=None) -> List[Dict[str, Any]]:
    """
    Search multiple Shopify stores and return aggregated results - SIMPLIFIED ONE STORE AT A TIME
    
    Args:
        store_domains: List of ALREADY VALIDATED Shopify domains
        query: Search query  
        max_results: Maximum total results to return
        product_callback: Optional callback function to stream products as they're found
        
    Returns:
        Aggregated list of products from all stores
    """
    if not store_domains or not query.strip():
        return []
    
    print(f"🚀 Starting SIMPLIFIED search for '{query}' across {len(store_domains)} stores...")
    print(f"⚡ Processing ONE STORE AT A TIME (no batching)")
    
    # Skip validation - domains are already validated by discovery service
    valid_domains = store_domains  # Use domains as-is since they're already validated
    
    # Search each store - ONE AT A TIME with immediate LLM filtering
    all_filtered_products = []
    service = ShopifyJSONService()
    
    # LLM filter for individual store processing
    from .shopify.llm_filter import LLMProductFilter
    llm_filter = LLMProductFilter()
    
    results_per_store = max(10, max_results // len(valid_domains)) if valid_domains else 20
    
    for i, domain in enumerate(valid_domains):
        store_url = f"https://{domain}"
        stream_progress_update(f"🏪 [{i+1}/{len(valid_domains)}] Searching *[{domain}]({store_url})*...")
        
        try:
            # Get basic filtered products from this store
            print(f"   📦 Fetching products from {domain}...")
            basic_products = service.search_store_products(domain, query, results_per_store, None)  # We'll stream LLM-filtered products instead
            
            if basic_products:
                print(f"   🔍 Got {len(basic_products)} basic filtered products, applying LLM filter...")
                
                # Apply LLM filtering to THIS STORE'S products immediately
                llm_filtered = llm_filter.filter_products(basic_products, query)
                
                # Apply price filtering to LLM results before streaming
                if max_price and llm_filtered:
                    price_filtered = []
                    for product in llm_filtered:
                        try:
                            price_value = product.get('price_value', 0)
                            if price_value == 0 or price_value <= max_price:
                                price_filtered.append(product)
                        except (ValueError, TypeError):
                            price_filtered.append(product)  # Include if price parsing fails
                    
                    if len(price_filtered) != len(llm_filtered):
                        print(f"   💰 Price filter: {len(llm_filtered)} → {len(price_filtered)} products under ${max_price}")
                    
                    llm_filtered = price_filtered
                
                print(f"   🤖 LLM filter: {len(basic_products)} → {len(llm_filtered)} products selected")
                
                # DEBUG: Check if streaming will happen
                print(f"   🔍 DEBUG: Will try to stream {len(llm_filtered)} products...")
                
                # Add store-specific metadata
                for product in llm_filtered:
                    product['llm_refined'] = True
                    product['store_processed'] = domain
                
                # Add to final results
                all_filtered_products.extend(llm_filtered)
                
                # Stream to frontend immediately - CRITICAL FOR REAL-TIME UPDATES!
                print(f"   🔍 DEBUG: About to check if streaming should happen. Products to stream: {len(llm_filtered)}")
                if llm_filtered:
                    try:
                        print(f"   📡 Streaming {len(llm_filtered)} LLM-filtered products to frontend...")
                        
                        # Use global streaming callback for real-time updates
                        from .progress_utils import get_streaming_callback
                        global_callback = get_streaming_callback()
                        
                        print(f"   🔧 DEBUG: Global callback available: {global_callback is not None}")
                        
                        if global_callback:
                            print(f"   🔧 DEBUG: About to loop through {len(llm_filtered)} products...")
                            for i, product in enumerate(llm_filtered):
                                print(f"   🔧 DEBUG: Processing product {i+1}/{len(llm_filtered)}: {product.get('product_name', 'Unknown')[:30]}...")
                                
                                # Create product data for streaming
                                product_data = {
                                    'type': 'product',
                                    'product_name': product.get('product_name', 'Unknown Product'),
                                    'price': product.get('price', 'Price not available'),
                                    'price_value': product.get('price_value', 0),
                                    'image_url': product.get('image_url', ''),
                                    'product_url': product.get('product_url', ''),
                                    'store': product.get('store_name', 'Unknown Store'),  # Frontend expects 'store' field
                                    'store_name': product.get('store_name', 'Unknown Store'),  # Keep for backend compatibility
                                    'description': product.get('description', ''),
                                    'source': product.get('source', 'shopify_json'),
                                    'marketplace': product.get('marketplace', 'SHOPIFY'),
                                    'is_available': product.get('is_available', True),
                                    'id': f"product-{product.get('product_name', '')}-{product.get('store_name', '')}"
                                }
                                
                                print(f"   🔧 DEBUG: About to call global_callback for product {i+1}...")
                                # Stream to frontend immediately
                                try:
                                    global_callback("product", product_data)
                                    print(f"   🔧 DEBUG: Successfully called global_callback for product {i+1}")
                                except Exception as e:
                                    print(f"   ❌ ERROR: global_callback failed for product {i+1}: {e}")
                                    break
                            
                            print(f"   ✅ Successfully streamed {len(llm_filtered)} products via global callback")
                        else:
                            print(f"   ⚠️  No global streaming callback available")
                        
                        # Also call the local callback if provided
                        if product_callback:
                            for product in llm_filtered:
                                product_callback(product)
                                
                    except Exception as e:
                        print(f"   ⚠️  Product streaming error: {e}")
                else:
                    print(f"   ⚠️  No LLM-filtered products to stream (count: {len(llm_filtered)})")
                
                print(f"   ✅ Store complete: {len(llm_filtered)} products (total: {len(all_filtered_products)})")
                
                # Stop if we have enough results
                if len(all_filtered_products) >= max_results:
                    print(f"   🎯 Reached target of {max_results} products, stopping search")
                    break
            else:
                print(f"   ❌ No products found in {domain}")
                
        except Exception as e:
            print(f"   ❌ Error processing {domain}: {e}")
            continue
    
    # Final processing
    print(f"⚡ Final processing: {len(all_filtered_products)} LLM-filtered products from {i+1} stores")
    
    # Remove duplicates based on product URL
    unique_products = []
    seen_urls = set()
    for product in all_filtered_products:
        url = product.get('product_url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_products.append(product)
        elif not url:
            # Include products without URLs (shouldn't happen, but be safe)
            unique_products.append(product)
    
    print(f"   🔧 Deduplication: {len(all_filtered_products)} → {len(unique_products)} unique products")
    
    # Sort by relevance score (higher is better)
    unique_products.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    # Limit results
    final_results = unique_products[:max_results]
    print(f"✅ SIMPLIFIED search complete: {len(final_results)} final results")
    
    return final_results 