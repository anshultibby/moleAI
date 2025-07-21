#!/usr/bin/env python3
"""
Test speed improvements and progress indicators
"""

import os
import sys
import time

# Add the app directory to the path
sys.path.append('app')

from app.utils.hybrid_search_service import HybridSearchService

def test_speed_improvements():
    """Test the speed improvements and progress indicators"""
    
    print("⚡ SPEED IMPROVEMENTS TEST")
    print("=" * 60)
    
    query = "black leggings"
    max_results = 20
    
    print(f"Testing query: '{query}'")
    print(f"Max results: {max_results}")
    print(f"Expected improvements:")
    print(f"   ⚡ Better progress indicators")
    print(f"   🚀 Faster domain validation")
    print(f"   📦 Progress during product fetching")
    print(f"   ⏱️  Reduced timeouts for speed")
    print(f"   📊 Step-by-step progress")
    
    print(f"\n🚀 Starting timed search...")
    start_time = time.time()
    
    try:
        hybrid = HybridSearchService()
        
        import asyncio
        
        async def run_search():
            return await hybrid.search(query, max_results=max_results, include_amazon=False)
        
        result = asyncio.run(run_search())
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print(f"\n📊 SPEED TEST RESULTS:")
        print(f"   ⏱️  Total time: {search_time:.1f}s")
        print(f"   🎯 Products found: {len(result.products)}")
        print(f"   🏪 Stores searched: {result.total_stores_searched}")
        print(f"   📊 Sources: {result.sources_used}")
        
        # Speed benchmarks
        if search_time < 30:
            print(f"   ✅ FAST: Under 30 seconds")
        elif search_time < 60:
            print(f"   ⚠️  MODERATE: {search_time:.1f}s (could be faster)")
        else:
            print(f"   ❌ SLOW: {search_time:.1f}s (needs optimization)")
        
        # Check if we got reasonable results
        if len(result.products) > 0:
            print(f"   ✅ Found products successfully")
            
            print(f"\n📋 Sample Results:")
            for i, product in enumerate(result.products[:3], 1):
                name = product.get('product_name', 'Unknown')[:40]
                store = product.get('store_name', 'Unknown Store')
                price = product.get('price', 'N/A')
                print(f"      {i}. {name}... - {price} from {store}")
        else:
            print(f"   ⚠️  No products found")
        
        print(f"\n🎯 Progress Indicators Check:")
        print(f"   ✅ Should see '🔍 Discovering Shopify stores...'")
        print(f"   ✅ Should see domain validation progress")
        print(f"   ✅ Should see individual store search progress")
        print(f"   ✅ Should see product fetching progress")
        print(f"   ✅ Should see final results summary")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_individual_store_speed():
    """Test individual store search speed"""
    
    print(f"\n" + "=" * 60)
    print(f"⚡ INDIVIDUAL STORE SPEED TEST")
    print("=" * 60)
    
    from app.utils.shopify_json_service import ShopifyJSONService
    
    service = ShopifyJSONService()
    test_store = "barrys-bootcamp-shop.myshopify.com"
    query = "black leggings"
    
    print(f"Testing store: {test_store}")
    print(f"Query: '{query}'")
    
    start_time = time.time()
    
    try:
        products = service.search_store_products(test_store, query, limit=10)
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print(f"\n📊 Individual Store Results:")
        print(f"   ⏱️  Time: {search_time:.1f}s")
        print(f"   🎯 Products: {len(products)}")
        
        if search_time < 10:
            print(f"   ✅ FAST: Under 10 seconds per store")
        elif search_time < 20:
            print(f"   ⚠️  MODERATE: {search_time:.1f}s per store")
        else:
            print(f"   ❌ SLOW: {search_time:.1f}s per store")
            
        print(f"\n📋 Expected Progress Messages:")
        print(f"   ✅ Should see '📄 Fetching products from {test_store}...'")
        print(f"   ✅ Should see '📦 Got X raw products, converting...'")
        print(f"   ✅ Should see '🔧 Converted to X available products, filtering...'")
        print(f"   ✅ Should see '✅ Final: X relevant products'")
        
    except Exception as e:
        print(f"❌ Individual store test failed: {e}")

if __name__ == "__main__":
    test_speed_improvements()
    test_individual_store_speed() 