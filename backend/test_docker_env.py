#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables the exact same way the app does
load_dotenv()

def test_env_and_api():
    """Test environment variables and API configuration exactly like the app"""
    
    print("🔧 Testing Environment & API Configuration")
    print("=" * 50)
    
    # Check all environment variables
    print("Environment Variables:")
    exa_key = os.getenv('EXA_API_KEY')
    jina_key = os.getenv('JINA_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
    
    print(f"  EXA_API_KEY: {'✅ Set' if exa_key else '❌ Missing'}")
    if exa_key:
        print(f"    Value: {exa_key[:10]}...{exa_key[-4:]}")
    
    print(f"  JINA_API_KEY: {'✅ Set' if jina_key else '❌ Missing'}")
    print(f"  GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Missing'}")
    print(f"  FIRECRAWL_API_KEY: {'✅ Set' if firecrawl_key else '❌ Missing'}")
    
    # Test Exa service initialization exactly like the app
    print("\n🔍 Testing Exa Service Initialization:")
    try:
        from app.utils.exa_service import ExaService
        
        # Initialize without passing key (let it use env var)
        exa1 = ExaService()
        print("✅ ExaService() - default initialization successful")
        
        # Initialize with explicit key
        exa2 = ExaService(exa_key)
        print("✅ ExaService(api_key) - explicit initialization successful")
        
        # Test the exact query from the logs
        query = "green metallic office cabinet under $200 buy online store price"
        print(f"\n🔍 Testing query: '{query}'")
        
        results = exa1.search(
            query=query,
            num_results=5,
            type="neural",
            include_text=True,
            text_type="text"
        )
        
        print(f"Results: {len(results)}")
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. {result.title[:60]}...")
            print(f"     URL: {result.url}")
            print(f"     Score: {result.score}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test hybrid search initialization
    print("\n🔍 Testing Hybrid Search Initialization:")
    try:
        from app.utils.hybrid_search_service import HybridSearchService
        
        # Initialize without passing keys
        hybrid1 = HybridSearchService()
        print("✅ HybridSearchService() - default initialization successful")
        
        # Test search
        results = hybrid1.search_products(
            query="green metallic office cabinet under $200",
            num_results=3,
            max_price=200,
            extract_content=False  # Skip content extraction for speed
        )
        
        print(f"Hybrid search results: {len(results)}")
        for i, result in enumerate(results[:2]):
            print(f"  {i+1}. {result.get('product_name', 'No name')}")
            print(f"     Store: {result.get('store_name', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_env_and_api() 