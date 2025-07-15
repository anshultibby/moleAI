#!/usr/bin/env python3
"""
Test script for Firecrawl integration
Run this to test if the Firecrawl service is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.firecrawl_service import FirecrawlService
from app.utils.gemini_tools_converter import ShoppingContextVariables, _search_product

def test_firecrawl_service():
    """Test the Firecrawl service directly"""
    print("Testing Firecrawl service...")
    
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
        
        # Test search with clothing query
        print("\n🔍 Testing Zara search for 'dresses'...")
        results = service.search_products("dresses")
        
        if results:
            print(f"✅ Successfully scraped Zara!")
            for result in results:
                print(f"  Source: {result.get('source', 'N/A')}")
                print(f"  Query: {result.get('query', 'N/A')}")
                print(f"  URL: {result.get('url', 'N/A')}")
                print(f"  Markdown length: {len(result.get('markdown', ''))}")
                print(f"  Title: {result.get('metadata', {}).get('title', 'N/A')}")
                
                # Show a snippet of the markdown
                markdown = result.get('markdown', '')
                if markdown:
                    snippet = markdown[:200] + "..." if len(markdown) > 200 else markdown
                    print(f"  Content snippet: {snippet}")
        else:
            print("⚠️ No results returned from Zara")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Firecrawl service: {str(e)}")
        return False

def test_search_product_function():
    """Test the search_product function integration"""
    print("\n" + "="*50)
    print("Testing search_product function integration...")
    
    # Create context
    context = ShoppingContextVariables()
    
    # Test arguments with clothing query
    arguments = {
        "query": "black dress",
        "max_price": 100,
        "category": "clothing"
    }
    
    try:
        result = _search_product(arguments, context)
        print(f"✅ Function result: {result}")
        print(f"✅ Deals found: {len(context.deals_found)}")
        
        if context.deals_found:
            print("\nDeals in context:")
            for i, deal in enumerate(context.deals_found[:3], 1):
                print(f"  {i}. {deal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing search_product function: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Starting Firecrawl Integration Tests (Zara Focus)")
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
        print("\n🎉 All tests passed! Firecrawl integration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
        print("\nTroubleshooting:")
        print("1. Make sure FIRECRAWL_API_KEY is set in your .env file")
        print("2. Check that your Firecrawl API key is valid and has credits")
        print("3. Verify internet connection for API calls") 