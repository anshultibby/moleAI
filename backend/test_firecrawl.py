#!/usr/bin/env python3
"""
Test script for Firecrawl integration with multi-store support
Run this to test if the Firecrawl service is working correctly across multiple e-commerce sites
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.firecrawl_service import FirecrawlService
from app.utils.gemini_tools_converter import ShoppingContextVariables, _search_product

def test_firecrawl_service():
    """Test the Firecrawl service directly with Google search capabilities"""
    print("Testing Firecrawl service with Google search integration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is configured
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("❌ FIRECRAWL_API_KEY not found in environment variables")
        return False
    
    print(f"✅ Found Firecrawl API key: {api_key[:8]}...")
    
    try:
        # Initialize service
        service = FirecrawlService(api_key)
        
        # Test Google-powered search (default behavior)
        print("\n🔍 Testing Google-powered search for 'winter jacket'...")
        results = service.search_products("winter jacket")
        
        if results:
            print(f"✅ Google search successful! Found results from {len(results)} stores:")
            for i, result in enumerate(results, 1):
                store_name = result.get('store_name', 'Unknown')
                source = result.get('source', 'Unknown')
                content_length = len(result.get('markdown', ''))
                print(f"  {i}. {store_name} ({source}) - {content_length} chars of content")
            
            # Test specific store search (fallback to known sites)
            print("\n🔍 Testing specific store search (Zara only)...")
            zara_results = service.search_products("black dress", sites=["zara"])
            if zara_results:
                print(f"✅ Zara-specific search successful! Found {len(zara_results)} result(s)")
            else:
                print("⚠️ No results from Zara-specific search")
            
            # Test fallback to known sites
            print("\n🔍 Testing fallback to known sites...")
            fallback_results = service.search_products_known_sites("sneakers", max_sites=2)
            if fallback_results:
                print(f"✅ Fallback search successful! Found {len(fallback_results)} result(s)")
            else:
                print("⚠️ No results from fallback search")
            
            return True
        else:
            print("⚠️ No results found from Google search, testing fallback...")
            
            # Test fallback if Google search fails
            fallback_results = service.search_products_known_sites("winter jacket", max_sites=2)
            if fallback_results:
                print(f"✅ Fallback to known sites successful! Found {len(fallback_results)} result(s)")
                return True
            else:
                print("❌ Both Google search and fallback failed")
                return False
            
    except Exception as e:
        print(f"❌ Error testing Firecrawl service: {str(e)}")
        return False

def test_search_product_function():
    """Test the search_product function integration with multi-store support"""
    print("\n" + "="*50)
    print("Testing search_product function integration with multi-store...")
    
    # Create context
    context = ShoppingContextVariables()
    
    # Test arguments with clothing query (multi-store)
    print("\n🔍 Testing multi-store search via function...")
    arguments = {
        "query": "black dress",
        "max_price": 100,
        "category": "clothing"
    }
    
    try:
        result = _search_product(arguments, context)
        print(f"✅ Multi-store function result length: {len(result)} characters")
        print(f"✅ Deals found: {len(context.deals_found)}")
        
        if context.deals_found:
            print("\nDeals in context (showing first 2):")
            for i, deal in enumerate(context.deals_found[:2], 1):
                store_name = deal.get('store_name', 'Unknown')
                source = deal.get('source', 'Unknown')
                print(f"  {i}. Store: {store_name} ({source})")
        
        # Test specific store search
        print("\n🔍 Testing specific store search via function...")
        context2 = ShoppingContextVariables()
        arguments2 = {
            "query": "sweater",
            "sites": ["H&M", "Uniqlo"]
        }
        
        result2 = _search_product(arguments2, context2)
        print(f"✅ Specific stores function result length: {len(result2)} characters")
        print(f"✅ Deals found: {len(context2.deals_found)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing search_product function: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Starting Firecrawl Integration Tests (Multi-Store Support)")
    print("="*50)
    
    # Test 1: Direct service test
    service_test = test_firecrawl_service()
    
    # Test 2: Function integration test
    function_test = test_search_product_function()
    
    print("\n" + "="*50)
    print("📊 Test Results:")
    print(f"  Firecrawl Service: {'✅ PASS' if service_test else '❌ FAIL'}")
    print(f"  Function Integration: {'✅ PASS' if function_test else '❌ FAIL'}")
    
    if service_test and function_test:
        print("\n🎉 All tests passed! Multi-store Firecrawl integration is working correctly.")
        print("\n📋 Supported stores:")
        print("  1. Zara (priority 1)")
        print("  2. H&M (priority 2)")
        print("  3. Uniqlo (priority 3)")
        print("  4. Forever 21 (priority 4)")
        print("  5. ASOS (priority 5)")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
        print("\nTroubleshooting:")
        print("1. Make sure FIRECRAWL_API_KEY is set in your .env file")
        print("2. Check that your Firecrawl API key is valid and has credits")
        print("3. Verify internet connection for API calls")
        print("4. Some stores may block scraping - this is normal") 