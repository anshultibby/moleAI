#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from app.utils.exa_service import ExaService
import json

def test_specific_queries():
    """Test the specific queries that are failing"""
    
    # Check API key
    api_key = os.getenv('EXA_API_KEY')
    if not api_key:
        print("❌ EXA_API_KEY not found in environment")
        return
    
    print(f"✅ EXA_API_KEY found: {api_key[:10]}...")
    
    # Initialize Exa service
    try:
        exa = ExaService(api_key)
        print("✅ Exa service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Exa service: {e}")
        return
    
    # Test queries that are failing
    test_queries = [
        "green metallic office cabinet under $200",
        "green metallic office cabinet",
        "office cabinet green",
        "metal office cabinet",
        "storage cabinet",
        "filing cabinet"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("=" * 50)
        
        try:
            # Test with different parameters
            print("1. Basic neural search:")
            results1 = exa.search(
                query=query,
                num_results=5,
                type="neural",
                include_text=True,
                text_type="text"
            )
            print(f"   Results: {len(results1)}")
            for i, result in enumerate(results1[:2]):
                print(f"   {i+1}. {result.title[:60]}...")
                print(f"      URL: {result.url}")
            
            print("\n2. Shopping sites search:")
            results2 = exa.search_shopping_sites(
                product_query=query,
                num_results=5
            )
            print(f"   Results: {len(results2)}")
            for i, result in enumerate(results2[:2]):
                print(f"   {i+1}. {result.title[:60]}...")
                print(f"      URL: {result.url}")
            
            print("\n3. Keyword search:")
            results3 = exa.search(
                query=query,
                num_results=5,
                type="keyword",
                include_text=True
            )
            print(f"   Results: {len(results3)}")
            for i, result in enumerate(results3[:2]):
                print(f"   {i+1}. {result.title[:60]}...")
                print(f"      URL: {result.url}")
                
        except Exception as e:
            print(f"❌ Error with query '{query}': {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_specific_queries() 