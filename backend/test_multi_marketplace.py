#!/usr/bin/env python3
"""
Test Multi-Marketplace Search
Shopify + Walmart + Target + Amazon via enhanced hybrid search
"""

import os
import sys
import asyncio
import time
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append('app')

from utils.hybrid_search_service import HybridSearchService
from utils.rye_service import RyeAPIService

load_dotenv()

async def test_multi_marketplace():
    """Test the new multi-marketplace search"""
    
    print("🛒 TESTING MULTI-MARKETPLACE SEARCH")
    print("=" * 60)
    
    # Check environment
    rye_key = os.getenv("RYE_API_KEY")
    google_cse = os.getenv("GOOGLE_CSE_API_KEY")
    
    print("🔧 Environment Check:")
    print(f"  {'✅' if rye_key else '❌'} RYE_API_KEY: {'Set' if rye_key else 'Missing'}")
    print(f"  {'✅' if google_cse else '❌'} GOOGLE_CSE_API_KEY: {'Set' if google_cse else 'Missing'}")
    
    if not rye_key:
        print("❌ Cannot test marketplaces without RYE_API_KEY")
        return
    
    print("\n" + "=" * 60)
    
    # Test queries across different categories
    test_cases = [
        {
            "query": "baby stroller",
            "expected_sources": ["shopify_json", "rye_walmart", "rye_target"],
            "category": "Baby Products"
        },
        {
            "query": "wireless headphones", 
            "expected_sources": ["shopify_json", "rye_walmart", "rye_amazon"],
            "category": "Electronics"
        },
        {
            "query": "winter coat kids",
            "expected_sources": ["shopify_json", "rye_target", "rye_walmart"], 
            "category": "Clothing"
        }
    ]
    
    service = HybridSearchService()
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        category = test_case["category"]
        
        print(f"\n🔍 TEST {i}: {category} - '{query}'")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Test enhanced search with marketplaces
            result = await service.search(query, max_results=15, include_marketplaces=True)
            
            end_time = time.time()
            
            print(f"⏱️  Completed in {end_time - start_time:.2f}s")
            print(f"📊 Found {len(result.products)} products")
            print(f"🏪 Searched {result.total_stores_searched} stores")
            
            if result.products:
                print("\n🏆 Top 3 Results:")
                for j, product in enumerate(result.products[:3], 1):
                    print(f"  {j}. {product.get('product_name', 'N/A')}")
                    print(f"     💰 {product.get('price', 'N/A')}")
                    print(f"     🏪 {product.get('store_name', 'N/A')} ({product.get('marketplace', 'N/A')})")
                    print(f"     🔗 {product.get('source', 'N/A')}")
                    print()
            
            # Source breakdown
            print("📈 Sources Found:")
            for source, count in result.sources_used.items():
                print(f"  - {source}: {count} products")
            
            # Check coverage
            found_sources = set(result.sources_used.keys())
            expected_sources = set(test_case["expected_sources"])
            coverage = len(found_sources & expected_sources) / len(expected_sources) * 100
            print(f"🎯 Coverage: {coverage:.0f}% of expected sources")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_rye_marketplaces():
    """Test Rye marketplace integration directly"""
    
    print("\n🔧 TESTING RYE MARKETPLACE INTEGRATION")
    print("=" * 60)
    
    try:
        service = RyeAPIService()
        
        # Test individual marketplaces
        marketplaces = ["WALMART", "TARGET", "AMAZON"]
        query = "baby shoes"
        
        for marketplace in marketplaces:
            print(f"\n🏪 Testing {marketplace}...")
            try:
                products = service.search_marketplace_products(marketplace, query, limit=3)
                print(f"   ✅ Found {len(products)} products")
                
                if products:
                    for product in products[:2]:
                        print(f"   - {product.get('product_name', 'N/A')}: {product.get('price', 'N/A')}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Test multi-marketplace search
        print(f"\n🔄 Testing multi-marketplace search for '{query}'...")
        try:
            all_products = service.search_multi_marketplace(query, limit=10)
            print(f"   ✅ Total products: {len(all_products)}")
            
            # Show source breakdown
            sources = {}
            for product in all_products:
                source = product.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print("   📊 Source breakdown:")
            for source, count in sources.items():
                print(f"     - {source}: {count}")
                
        except Exception as e:
            print(f"   ❌ Multi-marketplace error: {e}")
            
    except Exception as e:
        print(f"❌ Rye service initialization failed: {e}")

async def test_specific_marketplaces():
    """Test targeted marketplace search"""
    
    print("\n🎯 TESTING TARGETED MARKETPLACE SEARCH") 
    print("=" * 60)
    
    service = HybridSearchService()
    
    test_scenarios = [
        {
            "name": "Shopify Only",
            "marketplaces": ["SHOPIFY"],
            "query": "artisan baby shoes"
        },
        {
            "name": "Big Box Retailers",
            "marketplaces": ["WALMART", "TARGET"],
            "query": "baby stroller"
        },
        {
            "name": "Everything", 
            "marketplaces": ["SHOPIFY", "WALMART", "TARGET", "AMAZON"],
            "query": "kids winter jacket"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📋 {scenario['name']}: {scenario['marketplaces']}")
        print(f"   Query: '{scenario['query']}'")
        
        try:
            result = await service.search_specific_marketplaces(
                scenario['query'], 
                scenario['marketplaces'], 
                max_results=10
            )
            
            print(f"   ✅ Found {len(result.products)} products in {result.search_time:.2f}s")
            print(f"   📊 Sources: {list(result.sources_used.keys())}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Enhanced Multi-Marketplace Search\n")
    
    # Test Rye marketplace integration first
    test_rye_marketplaces()
    
    # Test full multi-marketplace pipeline
    asyncio.run(test_multi_marketplace())
    
    # Test targeted searches
    asyncio.run(test_specific_marketplaces())
    
    print("\n🎉 Multi-marketplace testing completed!")
    print("\n🚀 BENEFITS:")
    print("• Shopify: Unique brands, fast JSON access")
    print("• Walmart: Budget-friendly, everyday essentials")  
    print("• Target: Popular brands, family products")
    print("• Amazon: Massive selection, reviews")
    print("• Combined: Best coverage across all price points!") 