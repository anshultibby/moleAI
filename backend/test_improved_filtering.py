#!/usr/bin/env python3
"""
Test improved product filtering to ensure we get more relevant results
"""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

from app.utils.shopify_json_service import ShopifyJSONService

def test_improved_filtering():
    """Test that improved filtering finds more relevant products"""
    
    print("🧪 Testing Improved Product Filtering")
    print("=" * 60)
    
    service = ShopifyJSONService()
    
    # Test with a domain that has many products
    test_domain = "barrys-bootcamp-shop.myshopify.com"  # From your logs
    test_query = "black leggings"
    
    print(f"Testing domain: {test_domain}")
    print(f"Query: '{test_query}'")
    print(f"Expected improvements:")
    print(f"   ✅ Process more than 15 products")
    print(f"   ✅ Find more relevant matches")
    print(f"   ✅ Better pre-filtering")
    print(f"   ✅ Less false negatives")
    
    try:
        # Test the search
        print(f"\n🔍 Running improved search...")
        products = service.search_store_products(test_domain, test_query, limit=10)
        
        print(f"\n📊 Results:")
        print(f"   🎯 Found {len(products)} relevant products")
        
        if products:
            print(f"\n✅ Products found:")
            for i, product in enumerate(products, 1):
                name = product.get('product_name', 'Unknown')
                price = product.get('price', 'N/A')
                score = product.get('relevance_score', 0)
                print(f"   {i}. {name}")
                print(f"      Price: {price}, Relevance: {score}")
                print(f"      URL: {product.get('product_url', 'N/A')}")
                print()
        else:
            print(f"   ⚠️  No products found - this might indicate:")
            print(f"      - Store doesn't have matching products")
            print(f"      - LLM is being too strict")
            print(f"      - Pre-filtering is too aggressive")
    
    except Exception as e:
        print(f"   ❌ Test failed: {e}")

def test_smart_prefiltering():
    """Test the smart pre-filtering functionality"""
    
    print(f"\n" + "=" * 60)
    print(f"🎯 Testing Smart Pre-filtering")
    print("=" * 60)
    
    service = ShopifyJSONService()
    
    # Create mock products to test pre-filtering
    mock_products = [
        {
            'product_name': 'Black High-Waisted Leggings',
            'product_type': 'Activewear',
            'tags': ['black', 'leggings', 'workout'],
            'vendor': 'Nike',
            'description': 'Perfect black leggings for working out'
        },
        {
            'product_name': 'Blue Denim Jeans',
            'product_type': 'Jeans', 
            'tags': ['blue', 'denim', 'casual'],
            'vendor': 'Levi\'s',
            'description': 'Classic blue jeans'
        },
        {
            'product_name': 'Black Yoga Pants',
            'product_type': 'Pants',
            'tags': ['black', 'yoga', 'stretchy'],
            'vendor': 'Lululemon',
            'description': 'Comfortable black yoga pants'
        },
        {
            'product_name': 'Red Running Shorts',
            'product_type': 'Shorts',
            'tags': ['red', 'running', 'athletic'],
            'vendor': 'Adidas',
            'description': 'Red athletic shorts for running'
        },
        {
            'product_name': 'Black Athletic Leggings Pro',
            'product_type': 'Leggings',
            'tags': ['black', 'athletic', 'professional'],
            'vendor': 'Under Armour',
            'description': 'Professional grade black athletic leggings'
        }
    ]
    
    query = "black leggings"
    
    print(f"Testing pre-filtering with query: '{query}'")
    print(f"Mock products: {len(mock_products)}")
    
    try:
        filtered_products = service._smart_prefilter_products(mock_products, query, max_products=3)
        
        print(f"\n📊 Pre-filtering Results:")
        print(f"   📥 Input: {len(mock_products)} products")
        print(f"   📤 Output: {len(filtered_products)} products")
        
        print(f"\n✅ Filtered products (should prioritize black leggings):")
        for i, product in enumerate(filtered_products, 1):
            name = product.get('product_name', 'Unknown')
            product_type = product.get('product_type', 'Unknown')
            tags = ', '.join(product.get('tags', []))
            print(f"   {i}. {name}")
            print(f"      Type: {product_type}")
            print(f"      Tags: {tags}")
            print()
        
        # Check if the right products were prioritized
        expected_products = ['Black High-Waisted Leggings', 'Black Athletic Leggings Pro', 'Black Yoga Pants']
        found_names = [p.get('product_name', '') for p in filtered_products]
        
        matches = sum(1 for expected in expected_products if expected in found_names)
        print(f"📈 Quality Check: {matches}/{len(expected_products)} expected products found")
        
        if matches >= 2:
            print(f"✅ Pre-filtering is working well!")
        else:
            print(f"⚠️  Pre-filtering might need adjustment")
            
    except Exception as e:
        print(f"❌ Pre-filtering test failed: {e}")

def main():
    """Run improved filtering tests"""
    
    print("🔗 Improved Product Filtering Test Suite")
    print("=" * 60)
    
    # Test overall improvements
    test_improved_filtering()
    
    # Test pre-filtering specifically  
    test_smart_prefiltering()
    
    print(f"\n📋 Summary of Improvements:")
    print(f"   🔢 Increased from 15 to 50 products for LLM processing")
    print(f"   🎯 Added smart pre-filtering to get better candidates")
    print(f"   📈 Increased products fetched per store (limit * 5)")
    print(f"   🔧 Fixed suspicious handle warnings for valid characters")
    print(f"   💪 Better scoring for relevance matching")

if __name__ == "__main__":
    main() 