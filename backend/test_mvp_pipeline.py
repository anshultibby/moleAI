"""
Test the complete MVP shopping pipeline
"""

import os
from dotenv import load_dotenv
from app.utils.shopping_pipeline import process_shopping_query_with_tools

load_dotenv()

def test_mvp_pipeline():
    """Test the complete 4-step MVP shopping pipeline"""
    print("🛍️ Testing MVP Shopping Pipeline")
    print("="*50)
    
    # Test query
    user_query = "wireless bluetooth headphones under $80"
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    exa_key = os.getenv('EXA_API_KEY')
    if not exa_key:
        print("❌ EXA_API_KEY not found in environment")
        return False
    
    print(f"🔍 Query: {user_query}")
    print(f"🔑 API Keys: Gemini ✓, Exa ✓")
    print()
    
    try:
        # Run the complete pipeline
        structured_products, messages, final_response = process_shopping_query_with_tools(
            user_query=user_query,
            api_key=api_key,
            max_iterations=10
        )
        
        print("🎯 PIPELINE RESULTS:")
        print(f"Structured Products: {len(structured_products)}")
        print(f"Messages Exchanged: {len(messages)}")
        print(f"Final Response: {final_response}")
        print()
        
        # Show some product results
        if structured_products:
            print("📦 SAMPLE PRODUCTS FOUND:")
            for i, product in enumerate(structured_products[:3], 1):
                print(f"\n{i}. {product.get('product_name', 'N/A')}")
                print(f"   Price: {product.get('price', 'N/A')}")
                print(f"   Store: {product.get('store', 'N/A')}")
                print(f"   URL: {product.get('product_url', 'N/A')}")
        else:
            print("⚠️ No structured products found")
        
        # Show message flow
        print("\n💬 MESSAGE FLOW:")
        for i, msg in enumerate(messages[-4:], 1):  # Show last 4 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200]
            print(f"{i}. {role.upper()}: {content}...")
        
        # Success criteria
        success = (
            len(structured_products) > 0 and
            final_response and
            len(final_response) > 10
        )
        
        print(f"\n✅ SUCCESS: {success}")
        return success
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_queries():
    """Test with different types of queries"""
    queries = [
        "laptop under $500 for students",
        "winter coat women",
        "running shoes nike"
    ]
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return False
    
    print("\n🔄 Testing Multiple Query Types:")
    print("="*50)
    
    results = []
    for query in queries:
        print(f"\n🔍 Testing: '{query}'")
        try:
            structured_products, messages, final_response = process_shopping_query_with_tools(
                user_query=query,
                api_key=api_key,
                max_iterations=8
            )
            
            success = len(structured_products) > 0 and bool(final_response)
            results.append(success)
            print(f"   Products found: {len(structured_products)}")
            print(f"   Response: {'✓' if final_response else '✗'}")
            print(f"   Result: {'PASS' if success else 'FAIL'}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results)
    print(f"\n📊 Overall Success Rate: {success_rate:.1%} ({sum(results)}/{len(results)})")
    
    return success_rate > 0.5

if __name__ == "__main__":
    print("Starting MVP Pipeline Tests...")
    
    # Test 1: Single comprehensive test
    test1_success = test_mvp_pipeline()
    
    # Test 2: Multiple query types
    test2_success = test_different_queries()
    
    print("\n" + "="*50)
    print("FINAL TEST RESULTS:")
    print(f"MVP Pipeline Test: {'PASS' if test1_success else 'FAIL'}")
    print(f"Multiple Queries Test: {'PASS' if test2_success else 'FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 MVP PIPELINE IS WORKING!")
        print("Ready for frontend integration.")
    else:
        print("\n⚠️ Some issues detected. Check logs above.") 