#!/usr/bin/env python3
"""
Test script for Rye API integration
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path so we can import our modules
sys.path.append('app')

load_dotenv()

def test_rye_api():
    """Test the Rye API service"""
    print("🧪 Testing Rye API Integration")
    print("=" * 50)
    
    # Check environment variables
    rye_api_key = os.getenv("RYE_API_KEY")
    rye_shopper_ip = os.getenv("RYE_SHOPPER_IP", "127.0.0.1")
    
    if not rye_api_key:
        print("❌ RYE_API_KEY not found in environment variables")
        print("Please add your Rye API key to the .env file:")
        print("RYE_API_KEY=your_api_key_here")
        print("RYE_SHOPPER_IP=127.0.0.1  # Optional, defaults to 127.0.0.1")
        return False
    
    print(f"✅ RYE_API_KEY found: {rye_api_key[:20]}...")
    print(f"✅ RYE_SHOPPER_IP: {rye_shopper_ip}")
    print()
    
    try:
        # Import our Rye service
        from app.utils.rye_service import RyeAPIService, search_products_with_rye
        
        print("1. Testing Rye API Service initialization...")
        service = RyeAPIService(rye_api_key, rye_shopper_ip)
        print("✅ Rye API Service initialized successfully")
        print()
        
        print("2. Testing domain-based product search...")
        print("   Searching amazon.com for products...")
        domain_products = service.search_products_by_domain("amazon.com", limit=3)
        
        if domain_products:
            print(f"✅ Found {len(domain_products)} products from amazon.com")
            for i, product in enumerate(domain_products, 1):
                print(f"   {i}. {product.get('product_name', 'N/A')} - {product.get('price', 'N/A')}")
        else:
            print("⚠️  No products found from amazon.com (this might be normal)")
        print()
        
        print("3. Testing query-based product search...")
        print("   Searching for 'headphones'...")
        query_products = search_products_with_rye(
            query="headphones",
            api_key=rye_api_key,
            shopper_ip=rye_shopper_ip,
            limit=5
        )
        
        if query_products:
            print(f"✅ Found {len(query_products)} products for 'headphones'")
            for i, product in enumerate(query_products, 1):
                print(f"   {i}. {product.get('product_name', 'N/A')} - {product.get('price', 'N/A')}")
                print(f"      Store: {product.get('store_name', 'N/A')}")
                print(f"      Marketplace: {product.get('marketplace', 'N/A')}")
        else:
            print("⚠️  No products found for 'headphones'")
        print()
        
        print("4. Testing shopping pipeline integration...")
        from app.utils.gemini_tools_converter import ShoppingContextVariables, _search_product
        
        context = ShoppingContextVariables()
        result = _search_product({
            "query": "bluetooth speakers",
            "max_price": 100,
            "marketplaces": ["AMAZON", "SHOPIFY"],
            "limit": 5
        }, context)
        
        print("Search result:")
        print(result)
        print()
        print(f"Products added to context: {len(context.deals_found)}")
        
        if context.deals_found:
            print("Sample products in context:")
            for i, product in enumerate(context.deals_found[:3], 1):
                print(f"   {i}. {product.get('product_name', 'N/A')} - {product.get('price', 'N/A')}")
        
        print()
        print("🎉 All tests completed successfully!")
        print("✅ Rye API integration is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_rye_api()
    if success:
        print("\n🚀 You can now use the Rye API for product search!")
    else:
        print("\n💡 Please check your configuration and try again.") 