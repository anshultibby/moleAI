"""
Test the exact search pipeline that the full system uses
"""

import os
from dotenv import load_dotenv
from app.utils.gemini_tools_converter import (
    ShoppingContextVariables,
    execute_function_with_context
)

# Load environment variables
load_dotenv()

def test_full_pipeline_search():
    """Test the exact search flow that happens in the full pipeline"""
    
    print("🔬 Testing Full Pipeline Search")
    print("=" * 50)
    
    # Test the exact same terms from your logs
    test_queries = [
        "metal office cabinet green",
        "office cabinet", 
        "wireless headphones",
        "laptop under 800"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Testing: '{query}'")
        print("-" * 30)
        
        # Create fresh context
        context = ShoppingContextVariables()
        
        # Prepare arguments exactly as the AI would
        arguments = {
            "query": query,
            "max_price": 500 if "under" not in query else 800,
            "category": None,
            "sites": None
        }
        
        print(f"Arguments: {arguments}")
        
        try:
            # Execute the exact same function call as the pipeline
            result = execute_function_with_context(
                "search_product", 
                arguments, 
                context
            )
            
            print(f"✅ Function result: {result[:200]}...")
            print(f"Products found: {len(context.deals_found)}")
            
            # Show sample results
            if context.deals_found:
                for i, deal in enumerate(context.deals_found[:3]):
                    name = deal.get('product_name', deal.get('name', 'Unknown'))
                    store = deal.get('store_name', 'Unknown Store')
                    price = deal.get('price', 'N/A')
                    print(f"  {i+1}. {name} - {price} from {store}")
            else:
                print("  ❌ No products found in context")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_step_by_step_debug():
    """Debug each step of the search process"""
    
    print("\n\n🔍 Step-by-Step Debug")
    print("=" * 50)
    
    query = "metal office cabinet green"
    
    print(f"🎯 Debugging query: '{query}'")
    
    # Step 1: Test Exa service directly
    print("\n1️⃣ Testing Exa service directly...")
    try:
        from app.utils.exa_service import ExaService
        exa_service = ExaService()
        exa_results = exa_service.search(query, num_results=5)
        print(f"   Exa results: {len(exa_results)}")
        if exa_results:
            print(f"   Sample: {exa_results[0].title}")
    except Exception as e:
        print(f"   ❌ Exa error: {e}")
    
    # Step 2: Test hybrid service directly  
    print("\n2️⃣ Testing hybrid service directly...")
    try:
        from app.utils.hybrid_search_service import search_products_hybrid
        hybrid_results = search_products_hybrid(
            query=query,
            num_results=5,
            extract_content=False  # Skip for speed
        )
        print(f"   Hybrid results: {len(hybrid_results)}")
        if hybrid_results:
            sample = hybrid_results[0]
            print(f"   Sample: {sample.get('name', 'N/A')} from {sample.get('store_name', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Hybrid error: {e}")
    
    # Step 3: Test the _search_product function directly
    print("\n3️⃣ Testing _search_product function...")
    try:
        from app.utils.gemini_tools_converter import _search_product
        context = ShoppingContextVariables()
        arguments = {"query": query, "max_price": None}
        
        result = _search_product(arguments, context)
        print(f"   _search_product result: {len(result)} chars")
        print(f"   Context products: {len(context.deals_found)}")
        if context.deals_found:
            print(f"   Sample product: {context.deals_found[0].get('name', 'N/A')}")
    except Exception as e:
        print(f"   ❌ _search_product error: {e}")
        import traceback
        traceback.print_exc()

def test_environment_check():
    """Check if all environment variables are set correctly"""
    
    print("\n\n🔧 Environment Check")
    print("=" * 50)
    
    # Check API keys
    exa_key = os.getenv('EXA_API_KEY')
    print(f"EXA_API_KEY: {'✅ Set' if exa_key else '❌ Missing'}")
    if exa_key:
        print(f"   Key starts with: {exa_key[:10]}...")
    
    # Check if imports work
    try:
        from app.utils.exa_service import ExaService
        print("✅ Exa service import: OK")
    except Exception as e:
        print(f"❌ Exa service import: {e}")
    
    try:
        from app.utils.hybrid_search_service import HybridSearchService
        print("✅ Hybrid service import: OK")
    except Exception as e:
        print(f"❌ Hybrid service import: {e}")
    
    try:
        from app.utils.jina_service import JinaReaderService
        print("✅ Jina service import: OK")
    except Exception as e:
        print(f"❌ Jina service import: {e}")

if __name__ == "__main__":
    test_environment_check()
    test_step_by_step_debug()
    test_full_pipeline_search()
    
    print("\n" + "=" * 60)
    print("🎯 ANALYSIS:")
    print("If this test finds results but your pipeline doesn't,")
    print("the issue might be:")
    print("1. Timing/caching issues")
    print("2. Different API key or environment")
    print("3. Request rate limiting")
    print("4. Context/conversation state differences") 