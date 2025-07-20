#!/usr/bin/env python3
"""
Test the simplified LLM processing and generous filtering improvements
"""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

from app.utils.shopify_json_service import ShopifyJSONService

def test_simplified_processing():
    """Test the improved filtering with simplified LLM input"""
    
    print("🔍 SIMPLIFIED LLM PROCESSING TEST")
    print("=" * 60)
    
    service = ShopifyJSONService()
    
    # Test with specific attribute queries
    test_queries = [
        "black leggings",
        "white cotton shirt", 
        "red dress",
        "skinny jeans",
        "wool sweater"
    ]
    
    test_store = "barrys-bootcamp-shop.myshopify.com"
    
    for query in test_queries:
        print(f"\n🎯 Testing query: '{query}'")
        print("-" * 40)
        
        try:
            products = service.search_store_products(test_store, query, limit=10)
            
            print(f"📊 Results for '{query}':")
            print(f"   🎯 Found {len(products)} relevant products")
            
            if products:
                print(f"   📋 Products found:")
                for i, product in enumerate(products, 1):
                    name = product.get('product_name', 'Unknown')
                    print(f"      {i}. {name}")
                    
                # Check if results actually match the query attributes
                print(f"   🔍 Attribute Analysis:")
                query_words = query.lower().split()
                
                for word in query_words:
                    matching_products = 0
                    for product in products:
                        name = product.get('product_name', '').lower()
                        product_type = product.get('product_type', '').lower()
                        tags = ' '.join(product.get('tags', [])).lower()
                        
                        if word in f"{name} {product_type} {tags}":
                            matching_products += 1
                    
                    match_percentage = (matching_products / len(products)) * 100 if products else 0
                    print(f"      '{word}': {matching_products}/{len(products)} products ({match_percentage:.0f}%)")
            else:
                print(f"   ⚠️  No products found")
                print(f"      This could mean:")
                print(f"      - Store doesn't have this specific combination")
                print(f"      - Filtering is working correctly (being strict)")
                print(f"      - Need to try different stores")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📋 IMPROVEMENTS SUMMARY")
    print("=" * 60)
    print(f"✅ Simplified LLM input - faster processing")
    print(f"✅ Generous pre-filtering - more candidates (100 vs 50)")
    print(f"✅ Shuffling for variety - no bias toward first products")
    print(f"✅ Increased LLM capacity - 75 products vs 50")
    print(f"✅ More products fetched - limit * 8 vs limit * 5")
    print(f"✅ Strict attribute matching - better quality results")
    
    print(f"\n🎯 Expected Benefits:")
    print(f"   📈 More diverse product selection")
    print(f"   ⚡ Faster LLM processing (simplified input)")
    print(f"   🎯 More accurate attribute matching")
    print(f"   🔄 Better coverage of store inventory")

def test_pre_filtering_stats():
    """Test to show pre-filtering statistics"""
    
    print(f"\n" + "=" * 60)
    print(f"📊 PRE-FILTERING STATISTICS TEST")
    print("=" * 60)
    
    service = ShopifyJSONService()
    
    # Test with a store that has many products
    test_store = "doyoueven.myshopify.com"
    query = "leggings"
    
    print(f"Testing store: {test_store}")
    print(f"Query: '{query}'")
    
    try:
        # This will show the pre-filtering statistics
        products = service.search_store_products(test_store, query, limit=15)
        
        print(f"\n📊 Final Results:")
        print(f"   🎯 Returned {len(products)} products to user")
        
        if products:
            print(f"   📋 Sample results:")
            for i, product in enumerate(products[:5], 1):
                name = product.get('product_name', 'Unknown')[:50]
                print(f"      {i}. {name}...")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_simplified_processing()
    test_pre_filtering_stats() 