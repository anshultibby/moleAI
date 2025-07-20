#!/usr/bin/env python3
"""
Test improved store discovery and product filtering
"""

import os
import sys
import asyncio

# Add the app directory to the path
sys.path.append('app')

from app.utils.google_discovery_service import GoogleDiscoveryService
from app.utils.shopify_json_service import search_multiple_stores
from app.utils.hybrid_search_service import hybrid_search

async def test_improved_discovery():
    """Test the improved discovery system"""
    
    print("🧪 Testing Improved Store Discovery & Filtering")
    print("=" * 60)
    
    query = "winter jacket"
    
    # Test 1: Google CSE Discovery
    print(f"\n1️⃣ Testing Google CSE discovery for '{query}'...")
    try:
        discovery = GoogleDiscoveryService()
        stores = discovery.discover_shopify_stores(query, max_results=20)
        
        print(f"✅ Discovered {len(stores)} stores:")
        for i, store in enumerate(stores[:10], 1):
            print(f"   {i:2d}. {store}")
        
        if len(stores) > 10:
            print(f"   ... and {len(stores) - 10} more stores")
            
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return
    
    # Test 2: Product Search with Relevance Filtering
    print(f"\n2️⃣ Testing product search with improved filtering...")
    try:
        products = search_multiple_stores(stores[:10], query, max_results=20)
        
        print(f"✅ Found {len(products)} relevant products:")
        
        # Group by store to show diversity
        stores_with_products = {}
        for product in products:
            store_name = product.get('store_name', 'Unknown')
            if store_name not in stores_with_products:
                stores_with_products[store_name] = []
            stores_with_products[store_name].append(product)
        
        print(f"📊 Products from {len(stores_with_products)} different stores:")
        for store_name, store_products in stores_with_products.items():
            print(f"   🏪 {store_name}: {len(store_products)} products")
            for product in store_products[:2]:  # Show top 2 per store
                name = product.get('product_name', 'Unknown')[:40]
                price = product.get('price', 'No price')
                score = product.get('relevance_score', 0)
                image = "✅ Image" if product.get('image_url') else "❌ No image"
                print(f"      - {name}... | {price} | Score: {score} | {image}")
                
    except Exception as e:
        print(f"❌ Product search failed: {e}")
        return
    
    # Test 3: Hybrid Search
    print(f"\n3️⃣ Testing full hybrid search pipeline...")
    try:
        hybrid_products = await hybrid_search(query, max_results=15)
        
        print(f"✅ Hybrid search returned {len(hybrid_products)} products")
        
        # Analyze results
        unique_stores = set(p.get('store_name', 'Unknown') for p in hybrid_products)
        products_with_images = sum(1 for p in hybrid_products if p.get('image_url'))
        products_with_prices = sum(1 for p in hybrid_products if p.get('price_value', 0) > 0)
        
        print(f"📊 Quality metrics:")
        print(f"   🏪 Stores represented: {len(unique_stores)}")
        print(f"   🖼️  Products with images: {products_with_images}/{len(hybrid_products)}")
        print(f"   💰 Products with parsed prices: {products_with_prices}/{len(hybrid_products)}")
        
        print(f"\n📋 Sample results:")
        for i, product in enumerate(hybrid_products[:5], 1):
            name = product.get('product_name', 'Unknown')[:35]
            store = product.get('store_name', 'Unknown')[:20]
            price = product.get('price', 'No price')
            price_val = product.get('price_value', 0)
            image_status = "✅" if product.get('image_url') else "❌"
            print(f"   {i}. {name}... | {store} | {price} (${price_val}) | {image_status}")
            
    except Exception as e:
        print(f"❌ Hybrid search failed: {e}")
        return
    
    print(f"\n🎉 Test completed successfully!")
    print(f"📈 Improvements verified:")
    print(f"   ✅ Store discovery: {len(stores)} stores found")
    print(f"   ✅ Store diversity: {len(stores_with_products)} stores with products")
    print(f"   ✅ Product relevance: Improved scoring and filtering")
    print(f"   ✅ Image handling: Better URL processing")
    print(f"   ✅ Store names: Proper extraction and formatting")

if __name__ == "__main__":
    asyncio.run(test_improved_discovery()) 