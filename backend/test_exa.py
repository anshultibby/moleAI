"""
Test script for Exa.ai API integration
"""

import os
from dotenv import load_dotenv
from app.utils.exa_service import ExaService, search_products_with_exa

# Load environment variables
load_dotenv()

def test_exa_basic_search():
    """Test basic Exa search functionality"""
    print("Testing basic Exa search...")
    
    try:
        service = ExaService()
        results = service.search("best winter coats 2024", num_results=5)
        
        print(f"Found {len(results)} results")
        for i, result in enumerate(results[:3]):
            print(f"\n{i+1}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Score: {result.score}")
            if result.text:
                print(f"   Text preview: {result.text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Error in basic search test: {e}")
        return False

def test_exa_shopping_search():
    """Test Exa shopping-specific search"""
    print("\n" + "="*50)
    print("Testing Exa shopping search...")
    
    try:
        results = search_products_with_exa(
            "wireless headphones under $100",
            num_results=5
        )
        
        print(f"Found {len(results)} shopping results")
        for i, result in enumerate(results[:3]):
            print(f"\n{i+1}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Score: {result.score}")
            if result.text:
                print(f"   Text preview: {result.text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Error in shopping search test: {e}")
        return False

def test_exa_specific_stores():
    """Test searching specific store domains"""
    print("\n" + "="*50)
    print("Testing specific store search...")
    
    try:
        results = search_products_with_exa(
            "laptop stand",
            specific_stores=["amazon.com", "target.com"],
            num_results=5
        )
        
        print(f"Found {len(results)} results from specific stores")
        for i, result in enumerate(results[:3]):
            print(f"\n{i+1}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Score: {result.score}")
        
        return True
        
    except Exception as e:
        print(f"Error in specific stores test: {e}")
        return False

if __name__ == "__main__":
    print("Starting Exa.ai API tests...")
    print(f"EXA_API_KEY present: {'EXA_API_KEY' in os.environ}")
    
    # Run tests
    basic_success = test_exa_basic_search()
    shopping_success = test_exa_shopping_search()
    stores_success = test_exa_specific_stores()
    
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print(f"Basic search: {'PASS' if basic_success else 'FAIL'}")
    print(f"Shopping search: {'PASS' if shopping_success else 'FAIL'}")
    print(f"Specific stores: {'PASS' if stores_success else 'FAIL'}")
    
    if all([basic_success, shopping_success, stores_success]):
        print("\nAll tests passed! Exa integration is working.")
    else:
        print("\nSome tests failed. Check your EXA_API_KEY and network connection.") 