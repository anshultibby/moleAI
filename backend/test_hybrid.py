"""
Test hybrid search service (Exa + Web Scraping)
"""

import os
from dotenv import load_dotenv
from app.utils.hybrid_search_service import search_products_hybrid

load_dotenv()

def test_hybrid_search():
    """Test the hybrid search functionality"""
    print("Testing hybrid search (Exa + Jina AI Reader)...")
    
    try:
        # Test with content extraction enabled
        results = search_products_hybrid(
            query="bluetooth headphones under $80",
            num_results=5,
            extract_content=True
        )
        
        print(f"\nFound {len(results)} enriched results:")
        
        for i, product in enumerate(results[:3], 1):
            print(f"\n{'='*60}")
            print(f"PRODUCT {i}:")
            print(f"Name: {product.get('product_name', 'N/A')}")
            print(f"Price: {product.get('price', 'N/A')}")
            print(f"Store: {product.get('store_name', 'N/A')}")
            print(f"URL: {product.get('url', 'N/A')}")
            print(f"Availability: {product.get('availability', 'N/A')}")
            print(f"Brand: {product.get('brand', 'N/A')}")
            print(f"Source: {product.get('source', 'N/A')}")
            
            if product.get('images'):
                print(f"Images: {len(product['images'])} found")
                print(f"Main image: {product.get('image_url', 'N/A')}")
            else:
                print("Images: None found")
            
            if product.get('description'):
                print(f"Description: {product['description'][:100]}...")
            
            # Show content extraction success
            if product.get('extracted_content'):
                print(f"✓ Successfully extracted content ({len(product['extracted_content'])} chars)")
            else:
                print("✗ No extracted content (may have failed)")
        
        return True
        
    except Exception as e:
        print(f"Error in hybrid search test: {e}")
        return False

def test_specific_stores():
    """Test search on specific stores"""
    print("\n" + "="*60)
    print("Testing specific store search...")
    
    try:
        results = search_products_hybrid(
            query="laptop stand",
            specific_stores=["target.com", "bestbuy.com"],
            num_results=3,
            extract_content=True
        )
        
        print(f"Found {len(results)} results from specific stores:")
        
        for product in results:
            print(f"\n- {product.get('product_name', 'N/A')} at {product.get('store_name', 'N/A')}")
            print(f"  Price: {product.get('price', 'N/A')}")
            print(f"  Source: {product.get('source', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"Error in specific stores test: {e}")
        return False

if __name__ == "__main__":
    print("Starting Hybrid Search Service tests...")
    print(f"EXA_API_KEY present: {'EXA_API_KEY' in os.environ}")
    
    # Run tests
    hybrid_success = test_hybrid_search()
    stores_success = test_specific_stores()
    
    print("\n" + "="*60)
    print("TEST RESULTS:")
    print(f"Hybrid search: {'PASS' if hybrid_success else 'FAIL'}")
    print(f"Specific stores: {'PASS' if stores_success else 'FAIL'}")
    
    if all([hybrid_success, stores_success]):
        print("\nAll tests passed! Hybrid service is working.")
    else:
        print("\nSome tests failed. Check the output above for details.") 