#!/usr/bin/env python3
"""
Test LLM-based product filtering vs rule-based filtering
"""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

from app.utils.shopify_json_service import ShopifyJSONService

def test_llm_vs_rules():
    """Test the difference between LLM and rule-based filtering"""
    
    print("🧪 Testing LLM vs Rule-Based Product Filtering")
    print("=" * 60)
    
    # Create mock products that would confuse rule-based systems
    mock_products = [
        {
            'product_name': 'Classic Denim Jacket - Blue',
            'product_type': 'Jacket',
            'vendor': 'Levi\'s',
            'tags': ['denim', 'casual', 'outerwear'],
            'description': 'Classic blue denim jacket perfect for layering',
            'price': '$89.99',
            'price_value': 89.99,
            'image_url': 'https://example.com/jacket1.jpg',
            'product_url': 'https://store.com/denim-jacket',
            'store_name': 'Fashion Store',
            'availability': 'in stock',
            'source': 'shopify_json'
        },
        {
            'product_name': 'Skinny Fit Denim Jeans - Dark Blue',
            'product_type': 'Jeans',
            'vendor': 'Levi\'s',
            'tags': ['denim', 'skinny', 'pants'],
            'description': 'Skinny fit denim jeans in dark blue wash',
            'price': '$79.99',
            'price_value': 79.99,
            'image_url': 'https://example.com/jeans1.jpg',
            'product_url': 'https://store.com/denim-jeans',
            'store_name': 'Fashion Store',
            'availability': 'in stock',
            'source': 'shopify_json'
        },
        {
            'product_name': 'Vintage Denim Shirt - Light Blue',
            'product_type': 'Shirt',
            'vendor': 'Wrangler',
            'tags': ['denim', 'vintage', 'shirt'],
            'description': 'Vintage style denim shirt in light blue',
            'price': '$59.99',
            'price_value': 59.99,
            'image_url': 'https://example.com/shirt1.jpg',
            'product_url': 'https://store.com/denim-shirt',
            'store_name': 'Fashion Store',
            'availability': 'in stock',
            'source': 'shopify_json'
        },
        {
            'product_name': 'Oversized Denim Jacket - Black',
            'product_type': 'Outerwear',
            'vendor': 'Urban Outfitters',
            'tags': ['denim', 'oversized', 'black'],
            'description': 'Trendy oversized black denim jacket',
            'price': '$95.99',
            'price_value': 95.99,
            'image_url': 'https://example.com/jacket2.jpg',
            'product_url': 'https://store.com/black-denim-jacket',
            'store_name': 'Urban Store',
            'availability': 'in stock',
            'source': 'shopify_json'
        },
        {
            'product_name': 'Denim Skirt - Mini Length',
            'product_type': 'Skirt',
            'vendor': 'H&M',
            'tags': ['denim', 'mini', 'skirt'],
            'description': 'Cute mini denim skirt for summer',
            'price': '$29.99',
            'price_value': 29.99,
            'image_url': 'https://example.com/skirt1.jpg',
            'product_url': 'https://store.com/denim-skirt',
            'store_name': 'Fashion Store',
            'availability': 'in stock',
            'source': 'shopify_json'
        }
    ]
    
    service = ShopifyJSONService()
    query = "denim jacket"
    
    print(f"🔍 Query: '{query}'")
    print(f"📦 Total products to filter: {len(mock_products)}")
    print("\nProducts available:")
    for i, product in enumerate(mock_products, 1):
        print(f"   {i}. {product['product_name']} ({product['product_type']})")
    
    # Test basic filtering (fallback method)
    print(f"\n1️⃣ Testing basic rule-based filtering...")
    basic_results = service._basic_filter_by_query(mock_products.copy(), query)
    
    print(f"   📊 Basic filtering: {len(mock_products)} → {len(basic_results)} products")
    print("   Results:")
    for product in basic_results:
        print(f"      ✓ {product['product_name']} (score: {product.get('relevance_score', 0)})")
    
    # Test LLM filtering
    print(f"\n2️⃣ Testing LLM-based filtering...")
    llm_results = service._llm_filter_products(mock_products.copy(), query)
    
    print(f"   📊 LLM filtering: {len(mock_products)} → {len(llm_results)} products")
    print("   Results:")
    for product in llm_results:
        print(f"      ✓ {product['product_name']} (score: {product.get('relevance_score', 0)})")
    
    # Analysis
    print(f"\n📈 Analysis:")
    print(f"   🤖 LLM Results: {len(llm_results)} products")
    print(f"   📋 Basic Results: {len(basic_results)} products")
    
    # Check for correct filtering (should only include jackets)
    correct_llm = sum(1 for p in llm_results if 'jacket' in p['product_type'].lower() or 'jacket' in p['product_name'].lower())
    correct_basic = sum(1 for p in basic_results if 'jacket' in p['product_type'].lower() or 'jacket' in p['product_name'].lower())
    
    print(f"   ✅ LLM correctly identified: {correct_llm}/{len(llm_results)} as jackets")
    print(f"   ✅ Basic correctly identified: {correct_basic}/{len(basic_results)} as jackets")
    
    if len(llm_results) < len(basic_results) and correct_llm >= correct_basic:
        print(f"\n🏆 LLM filtering is more precise!")
    elif correct_llm > correct_basic:
        print(f"\n🏆 LLM filtering is more accurate!")
    else:
        print(f"\n📊 Both methods performed similarly")

if __name__ == "__main__":
    test_llm_vs_rules() 