"""
Test Jina AI service with API key
"""

import os
from dotenv import load_dotenv
from app.utils.jina_service import JinaReaderService

# Load environment variables
load_dotenv()

def test_jina_api_key():
    """Test if Jina API key is working"""
    
    print("🧪 Testing Jina AI Service with API Key")
    print("=" * 50)
    
    # Check if API key exists
    jina_key = os.getenv('JINA_API_KEY')
    print(f"JINA_API_KEY: {'✅ Found' if jina_key else '❌ Missing'}")
    
    if jina_key:
        print(f"Key starts with: {jina_key[:10]}...")
    
    # Test without API key (free tier)
    print("\n🆓 Testing Free Tier (no API key):")
    try:
        service_free = JinaReaderService(api_key=None)
        result_free = service_free.read_url("https://www.amazon.com/dp/B08N5WRWNW")
        print(f"Free tier result: {len(result_free.get('content', '')) if result_free else 0} chars")
    except Exception as e:
        print(f"Free tier error: {e}")
    
    # Test with API key (premium)
    if jina_key:
        print("\n💎 Testing Premium Tier (with API key):")
        try:
            service_premium = JinaReaderService(api_key=jina_key)
            result_premium = service_premium.read_url("https://www.amazon.com/dp/B08N5WRWNW")
            print(f"Premium result: {len(result_premium.get('content', '')) if result_premium else 0} chars")
            
            if result_premium and result_premium.get('content'):
                content = result_premium['content']
                print(f"Sample content: {content[:200]}...")
        except Exception as e:
            print(f"Premium tier error: {e}")
    
    # Test the hybrid search with API key
    print("\n🔄 Testing Hybrid Search with Jina API Key:")
    try:
        from app.utils.hybrid_search_service import search_products_hybrid
        
        results = search_products_hybrid(
            query="wireless headphones",
            num_results=2,
            extract_content=True,  # This will use Jina
            jina_api_key=jina_key
        )
        
        print(f"Hybrid search results: {len(results)}")
        if results:
            for i, result in enumerate(results[:2]):
                name = result.get('name', 'Unknown')
                store = result.get('store_name', 'Unknown')
                content_length = len(result.get('extracted_content', ''))
                print(f"  {i+1}. {name} from {store} ({content_length} chars extracted)")
                
    except Exception as e:
        print(f"Hybrid search error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jina_api_key() 