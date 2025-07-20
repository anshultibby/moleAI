#!/usr/bin/env python3
"""
Debug the full pipeline to find example.com links and 12 result limit
"""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

from app.utils.hybrid_search_service import HybridSearchService
from app.utils.shopify_json_service import ShopifyJSONService, search_multiple_stores
from app.utils.google_discovery_service import GoogleDiscoveryService

def test_full_pipeline():
    """Test the full pipeline to debug issues"""
    
    print("🔍 FULL PIPELINE DEBUG TEST")
    print("=" * 60)
    
    query = "black leggings"
    
    # Test 1: Google Discovery
    print("\n1️⃣ TESTING GOOGLE DISCOVERY")
    print("-" * 40)
    
    discovery = GoogleDiscoveryService()
    stores = discovery.discover_shopify_stores(query, max_results=50)  # Test with increased limit
    
    print(f"📊 Discovery Results:")
    print(f"   🏪 Found {len(stores)} stores (target was 50)")
    print(f"   📋 First 10 stores:")
    
    for i, store in enumerate(stores[:10], 1):
        print(f"      {i}. {store}")
    
    if len(stores) > 10:
        print(f"   ... and {len(stores) - 10} more")
    
    # Check for any bad domains
    bad_domains = []
    for store in stores:
        if any(bad in store.lower() for bad in ['example.com', 'test.com', 'localhost', 'demo.com']):
            bad_domains.append(store)
    
    if bad_domains:
        print(f"   ⚠️  WARNING: Found {len(bad_domains)} potentially bad domains:")
        for domain in bad_domains:
            print(f"      - {domain}")
    else:
        print(f"   ✅ No bad domains found in discovery")
    
    # Test 2: Multiple Store Search
    print(f"\n2️⃣ TESTING MULTIPLE STORE SEARCH")
    print("-" * 40)
    
    # Use first 20 stores for testing
    test_stores = stores[:20]
    print(f"Testing with {len(test_stores)} stores...")
    
    all_products = search_multiple_stores(test_stores, query, max_results=100)  # Test with high limit
    
    print(f"\n📊 Multiple Store Search Results:")
    print(f"   🎯 Found {len(all_products)} total products")
    
    # Analyze product URLs for bad domains
    bad_products = []
    domain_counts = {}
    
    for product in all_products:
        product_url = product.get('product_url', '')
        image_url = product.get('image_url', '')
        store_name = product.get('store_name', 'Unknown')
        
        # Count domains
        if store_name not in domain_counts:
            domain_counts[store_name] = 0
        domain_counts[store_name] += 1
        
        # Check for bad URLs
        if any(bad in product_url.lower() for bad in ['example.com', 'test.com', 'localhost', 'demo.com']):
            bad_products.append((product.get('product_name', 'Unknown'), product_url, 'product_url'))
        
        if any(bad in image_url.lower() for bad in ['example.com', 'test.com', 'localhost', 'demo.com']):
            bad_products.append((product.get('product_name', 'Unknown'), image_url, 'image_url'))
    
    # Report results
    print(f"   🏪 Products by store:")
    sorted_stores = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
    for store, count in sorted_stores[:10]:
        print(f"      {store}: {count} products")
    
    if len(sorted_stores) > 10:
        print(f"      ... and {len(sorted_stores) - 10} more stores")
    
    if bad_products:
        print(f"\n   ⚠️  WARNING: Found {len(bad_products)} products with bad URLs:")
        for name, url, url_type in bad_products[:5]:  # Show first 5
            print(f"      - {name}: {url} ({url_type})")
        if len(bad_products) > 5:
            print(f"      ... and {len(bad_products) - 5} more")
    else:
        print(f"   ✅ No bad URLs found in products")
    
    # Test 3: Hybrid Search Service
    print(f"\n3️⃣ TESTING HYBRID SEARCH SERVICE")
    print("-" * 40)
    
    hybrid = HybridSearchService()
    
    import asyncio
    
    async def test_hybrid():
        result = await hybrid.search(query, max_results=50, include_amazon=False)  # Test with increased limit
        return result
    
    try:
        search_result = asyncio.run(test_hybrid())
        
        print(f"📊 Hybrid Search Results:")
        print(f"   🎯 Found {len(search_result.products)} products")
        print(f"   🏪 Searched {search_result.total_stores_searched} stores")
        print(f"   📊 Sources: {search_result.sources_used}")
        print(f"   ⏱️  Time: {search_result.search_time:.2f}s")
        
        # Check hybrid results for bad URLs
        hybrid_bad_products = []
        for product in search_result.products:
            product_url = product.get('product_url', '')
            image_url = product.get('image_url', '')
            
            if any(bad in product_url.lower() for bad in ['example.com', 'test.com', 'localhost', 'demo.com']):
                hybrid_bad_products.append((product.get('product_name', 'Unknown'), product_url, 'product_url'))
            
            if any(bad in image_url.lower() for bad in ['example.com', 'test.com', 'localhost', 'demo.com']):
                hybrid_bad_products.append((product.get('product_name', 'Unknown'), image_url, 'image_url'))
        
        if hybrid_bad_products:
            print(f"\n   ⚠️  WARNING: Found {len(hybrid_bad_products)} products with bad URLs in hybrid search:")
            for name, url, url_type in hybrid_bad_products:
                print(f"      - {name}: {url} ({url_type})")
        else:
            print(f"   ✅ No bad URLs found in hybrid search")
        
    except Exception as e:
        print(f"   ❌ Hybrid search failed: {e}")
    
    # Test 4: Individual Store Testing
    print(f"\n4️⃣ TESTING INDIVIDUAL STORE")
    print("-" * 40)
    
    # Test one specific store that was giving problems
    test_store = "barrys-bootcamp-shop.myshopify.com"
    print(f"Testing individual store: {test_store}")
    
    shopify_service = ShopifyJSONService()
    store_products = shopify_service.search_store_products(test_store, query, limit=50)  # Test with higher limit
    
    print(f"📊 Individual Store Results:")
    print(f"   🎯 Found {len(store_products)} products from {test_store}")
    
    if store_products:
        print(f"   📋 Sample products:")
        for i, product in enumerate(store_products[:3], 1):
            name = product.get('product_name', 'Unknown')
            price = product.get('price', 'N/A')
            url = product.get('product_url', 'N/A')
            print(f"      {i}. {name} - {price}")
            print(f"         URL: {url}")
    
    print(f"\n📋 SUMMARY")
    print("=" * 60)
    print(f"✅ Discovery found {len(stores)} stores (increased from 12 limit)")
    print(f"✅ Multiple store search found {len(all_products)} products")
    print(f"✅ Individual store test found {len(store_products)} products")
    
    if bad_products or hybrid_bad_products:
        print(f"⚠️  Found bad URLs - needs investigation")
    else:
        print(f"✅ No bad URLs found - filtering is working")
    
    print(f"\n🎯 The improvements should give you:")
    print(f"   📈 More stores discovered (up to 50 instead of 12)")
    print(f"   📈 More products per store (limit * 5)")
    print(f"   📈 Better LLM filtering (up to 50 products)")
    print(f"   🚫 No example.com or localhost URLs")

if __name__ == "__main__":
    test_full_pipeline() 