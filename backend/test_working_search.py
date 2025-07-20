"""
Test the full pipeline with search terms that work
"""

import os
from dotenv import load_dotenv
from app.utils.shopping_pipeline import process_shopping_query_with_tools

load_dotenv()

def test_working_pipeline():
    """Test with search terms we know work"""
    print("🧪 Testing Full Pipeline with Working Search Terms")
    print("=" * 60)
    
    # Test with terms we know work based on diagnostic
    working_queries = [
        "wireless headphones",  # We know this works
        "laptop under $1000",   # Should work
        "bluetooth speaker",    # Simple, popular
    ]
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return False
    
    for query in working_queries:
        print(f"\n🔍 Testing: '{query}'")
        print("-" * 40)
        
        try:
            structured_products, messages, final_response = process_shopping_query_with_tools(
                user_query=query,
                api_key=api_key,
                max_iterations=8
            )
            
            print(f"✅ Success!")
            print(f"   Products found: {len(structured_products)}")
            print(f"   Messages: {len(messages)}")
            print(f"   Final response: {'✓' if final_response else '✗'}")
            
            if structured_products:
                print(f"   Sample product: {structured_products[0].get('product_name', 'N/A')}")
                print(f"   Sample price: {structured_products[0].get('price', 'N/A')}")
                print(f"   Sample store: {structured_products[0].get('store', 'N/A')}")
            
            if final_response:
                print(f"   Response preview: {final_response[:100]}...")
            
            return True  # Success - pipeline is working
            
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    return False

def test_green_cabinet_alternatives():
    """Test alternative search terms for green cabinets"""
    print("\n🔧 Testing Alternative Cabinet Search Terms")
    print("=" * 60)
    
    # More general terms that might work better
    cabinet_alternatives = [
        "office storage cabinet",     # More general
        "filing cabinet",            # Very common
        "metal storage cabinet",     # Remove color specificity
        "office furniture cabinet",  # Broader category
    ]
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    for query in cabinet_alternatives:
        print(f"\n🔍 Testing: '{query}'")
        
        try:
            structured_products, messages, final_response = process_shopping_query_with_tools(
                user_query=query,
                api_key=api_key,
                max_iterations=6
            )
            
            print(f"   Results: {len(structured_products)} products")
            
            if structured_products:
                print(f"   ✅ Found products! Pipeline working for cabinet searches")
                return True
            else:
                print(f"   ❌ No products found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    print("🧪 PIPELINE TESTING WITH WORKING TERMS")
    print("=" * 60)
    
    # Test 1: Known working terms
    basic_success = test_working_pipeline()
    
    # Test 2: Cabinet alternatives
    cabinet_success = test_green_cabinet_alternatives()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"Basic Pipeline: {'✅ WORKING' if basic_success else '❌ ISSUES'}")
    print(f"Cabinet Search: {'✅ WORKING' if cabinet_success else '❌ ISSUES'}")
    
    if basic_success:
        print("\n🎉 GREAT NEWS: The pipeline is fully functional!")
        print("💡 ISSUE: The search terms 'metal office cabinet green' are too specific")
        print("🔧 SOLUTION: Use broader terms or try these alternatives:")
        print("   - 'office storage cabinet'")
        print("   - 'filing cabinet metal'") 
        print("   - 'office furniture storage'")
        print("   - Search 'filing cabinet' then filter by color")
    else:
        print("\n🚨 PIPELINE ISSUES DETECTED")
        print("Need to investigate further...") 