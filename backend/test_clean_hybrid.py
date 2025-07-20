#!/usr/bin/env python3
"""
Test the clean hybrid search pipeline
JSON-first approach with minimal fallbacks
"""

import os
import sys
import asyncio
import time
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append('app')

from utils.hybrid_search_service import HybridSearchService, hybrid_search
from utils.shopify_json_service import ShopifyJSONService, search_multiple_stores

load_dotenv()

async def test_clean_pipeline():
    """Test the clean JSON-first pipeline"""
    
    print("🚀 TESTING CLEAN HYBRID PIPELINE")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = ['GOOGLE_CSE_API_KEY', 'GOOGLE_CSE_ID']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
        print("JSON service will still work, but discovery will be limited")
    else:
        print("✅ All required environment variables set")
    
    print("\n" + "=" * 50)
    
    # Test queries
    test_queries = [
        "kids winter jackets", 
        "baby shoes",
        "wireless headphones"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 TEST {i}: '{query}'")
        print("-" * 30)
        
        start_time = time.time()
        
        try:
            # Use the main hybrid search function
            products = await hybrid_search(query, max_results=15)
            
            end_time = time.time()
            
            print(f"⏱️  Completed in {end_time - start_time:.2f}s")
            print(f"📊 Found {len(products)} products")
            
            if products:
                print("\n🏆 Top 3 Results:")
                for j, product in enumerate(products[:3], 1):
                    print(f"  {j}. {product.get('product_name', 'N/A')}")
                    print(f"     💰 {product.get('price', 'N/A')}")
                    print(f"     🏪 {product.get('store_name', 'N/A')}")
                    print(f"     🔗 {product.get('source', 'N/A')}")
                    print()
                
                # Source breakdown
                sources = {}
                for product in products:
                    source = product.get('source', 'unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                print("📈 Sources:")
                for source, count in sources.items():
                    print(f"  - {source}: {count}")
            else:
                print("❌ No products found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_direct_json():
    """Test direct JSON service"""
    
    print("\n🔧 TESTING DIRECT JSON SERVICE")
    print("=" * 50)
    
    service = ShopifyJSONService()
    
    # Test with known Shopify stores
    test_stores = [
        "shop.gymshark.com",
        "freshly-picked.myshopify.com", 
        "arctix1.myshopify.com"
    ]
    
    for store in test_stores:
        print(f"\n🏪 Testing {store}...")
        try:
            products = service.search_store_products(store, "kids", limit=5)
            print(f"   ✅ Found {len(products)} products")
            
            if products:
                for product in products[:2]:
                    print(f"   - {product.get('product_name', 'N/A')}: {product.get('price', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Clean Hybrid Search Pipeline\n")
    
    # Test direct JSON service first
    test_direct_json()
    
    # Test full pipeline
    asyncio.run(test_clean_pipeline())
    
    print("\n🎉 Testing completed!") 