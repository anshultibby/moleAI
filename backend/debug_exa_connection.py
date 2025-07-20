"""
Debug Exa API Connection
Test why searches are returning 0 results
"""

import os
from dotenv import load_dotenv
from app.utils.exa_service import ExaService

load_dotenv()

def test_exa_connection():
    """Test basic Exa API connection"""
    print("🔍 Testing Exa API Connection...")
    
    api_key = os.getenv('EXA_API_KEY')
    if not api_key:
        print("❌ EXA_API_KEY not found in environment")
        return False
    
    print(f"✅ EXA_API_KEY found: {api_key[:10]}...")
    
    try:
        service = ExaService(api_key)
        
        # Test with very basic queries first
        test_queries = [
            "headphones",
            "laptop", 
            "amazon products",
            "shopping",
            "buy online"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            try:
                results = service.search_shopping_sites(query, num_results=3)
                print(f"   Results: {len(results)}")
                
                if results:
                    for i, result in enumerate(results[:1], 1):
                        print(f"   {i}. {result.title[:50]}...")
                        print(f"      URL: {result.url}")
                    return True  # Found working query
                    
            except Exception as e:
                print(f"   Error: {e}")
        
        print("\n❌ All test queries returned 0 results")
        return False
        
    except Exception as e:
        print(f"❌ Exa service error: {e}")
        return False

def test_alternative_search():
    """Test with different search parameters"""
    print("\n🔧 Testing Alternative Search Parameters...")
    
    try:
        service = ExaService()
        
        # Test general web search (not shopping-specific)
        print("Testing general web search...")
        results = service.search(
            query="laptop reviews",
            num_results=3,
            type="neural",
            include_text=True
        )
        
        print(f"General search results: {len(results)}")
        if results:
            for result in results[:1]:
                print(f"- {result.title}")
                print(f"  {result.url}")
        
        # Test with different domains
        print("\nTesting with specific domains...")
        results = service.search(
            query="laptop",
            num_results=3,
            include_domains=["amazon.com"],
            type="neural"
        )
        
        print(f"Amazon-specific results: {len(results)}")
        if results:
            for result in results[:1]:
                print(f"- {result.title}")
                print(f"  {result.url}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"Alternative search error: {e}")
        return False

def test_api_status():
    """Test if Exa API is responding at all"""
    print("\n🏥 Testing API Health...")
    
    try:
        import requests
        
        # Test basic API endpoint
        api_key = os.getenv('EXA_API_KEY')
        response = requests.get(
            "https://api.exa.ai/search",
            params={
                "query": "test",
                "numResults": 1
            },
            headers={
                "accept": "application/json",
                "x-api-key": api_key
            },
            timeout=10
        )
        
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ Authentication failed - check API key")
        elif response.status_code == 429:
            print("❌ Rate limit exceeded")
        elif response.status_code == 200:
            data = response.json()
            results_count = len(data.get("results", []))
            print(f"✅ API working - found {results_count} results")
            return True
        else:
            print(f"❌ Unexpected status: {response.text}")
        
        return False
        
    except Exception as e:
        print(f"API health test error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Debugging Exa API Connection")
    print("=" * 50)
    
    # Run diagnostics
    connection_ok = test_exa_connection()
    alternative_ok = test_alternative_search()
    api_health_ok = test_api_status()
    
    print("\n" + "=" * 50)
    print("🔧 DIAGNOSTIC RESULTS:")
    print(f"Basic Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"Alternative Search: {'✅ PASS' if alternative_ok else '❌ FAIL'}")
    print(f"API Health: {'✅ PASS' if api_health_ok else '❌ FAIL'}")
    
    if not any([connection_ok, alternative_ok, api_health_ok]):
        print("\n🚨 RECOMMENDATIONS:")
        print("1. Check EXA_API_KEY validity")
        print("2. Verify API quota/billing")
        print("3. Check Exa.ai service status")
        print("4. Try different search terms")
        print("5. Consider using Scrapfly as backup")
    else:
        print("\n✅ Exa API is working - issue might be with specific search terms") 