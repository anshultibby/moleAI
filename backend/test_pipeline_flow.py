#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from app.utils.exa_service import ExaService
from app.utils.hybrid_search_service import search_products_hybrid

def test_pipeline_flow():
    """Test the exact flow used in the shopping pipeline"""
    
    # Test the exact query from your logs
    search_term = "green metallic office cabinet under $200"
    
    print(f"🔍 Testing pipeline flow for: '{search_term}'")
    print("=" * 60)
    
    # Step 1: Direct Exa call (as done in the pipeline)
    print("\n1. Direct Exa call (as in pipeline):")
    try:
        exa_service = ExaService()
        exa_query = f"{search_term} buy online store price"
        print(f"   Query: '{exa_query}'")
        
        exa_results = exa_service.search(
            query=exa_query,
            num_results=5,
            type="neural",
            include_text=True
        )
        
        print(f"   Results: {len(exa_results)}")
        for i, result in enumerate(exa_results[:3]):
            print(f"   {i+1}. {result.title[:60]}...")
            print(f"      URL: {result.url}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 2: Hybrid search call (as done in the pipeline)  
    print("\n2. Hybrid search call (as in pipeline):")
    try:
        results = search_products_hybrid(
            query=search_term,
            num_results=5,
            max_price=200,
            specific_stores=None,  # No specific stores
            extract_content=True
        )
        
        print(f"   Results: {len(results)}")
        for i, result in enumerate(results[:3]):
            print(f"   {i+1}. {result.get('product_name', 'No name')} - {result.get('price', 'No price')}")
            print(f"      Store: {result.get('store_name', 'Unknown')}")
            print(f"      URL: {result.get('url', 'No URL')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Let's test what query the hybrid search is actually making
    print("\n3. Debug: What query does hybrid search make?")
    try:
        from app.utils.hybrid_search_service import HybridSearchService
        
        hybrid_service = HybridSearchService()
        
        # This is what the hybrid search constructs internally
        search_query = f"{search_term} buy online store price"
        print(f"   Hybrid constructs query: '{search_query}'")
        
        # Test this query directly
        direct_results = hybrid_service.exa_service.search(
            query=search_query,
            num_results=5,
            type="neural",
            include_text=True,
            text_type="text"
        )
        
        print(f"   Direct call results: {len(direct_results)}")
        for i, result in enumerate(direct_results[:3]):
            print(f"   {i+1}. {result.title[:60]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline_flow() 