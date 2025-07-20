"""
Test Exa content retrieval for product pages
"""

import os
from dotenv import load_dotenv
from app.utils.exa_service import ExaService

load_dotenv()

def test_exa_content_quality():
    """Test what kind of content Exa provides for product pages"""
    print("Testing Exa content quality for product pages...")
    
    try:
        service = ExaService()
        
        # Search for a specific product
        results = service.search_shopping_sites(
            "wireless headphones under $100",
            num_results=3
        )
        
        print(f"Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"\n{'='*60}")
            print(f"RESULT {i}: {result.title}")
            print(f"URL: {result.url}")
            print(f"Score: {result.score}")
            print(f"Published: {result.published_date}")
            
            if result.text:
                print(f"\nContent length: {len(result.text)} characters")
                print(f"Content preview:")
                print("-" * 40)
                print(result.text[:1000])
                print("-" * 40)
                
                # Check for common e-commerce elements
                text_lower = result.text.lower()
                has_price = any(indicator in text_lower for indicator in ['$', 'price', 'cost', '£', '€'])
                has_product_info = any(indicator in text_lower for indicator in ['add to cart', 'buy now', 'in stock', 'product'])
                has_brand = any(indicator in text_lower for indicator in ['brand', 'model', 'manufacturer'])
                
                print(f"\nE-commerce indicators:")
                print(f"- Has price info: {has_price}")
                print(f"- Has product info: {has_product_info}")
                print(f"- Has brand info: {has_brand}")
            else:
                print("No text content available")
                
            if result.highlights:
                print(f"\nHighlights ({len(result.highlights)}):")
                for j, highlight in enumerate(result.highlights[:3]):
                    print(f"  {j+1}. {highlight}")
        
        # Test get_content method with specific URLs
        if results:
            print(f"\n{'='*60}")
            print("TESTING get_content method...")
            
            urls = [result.url for result in results[:2]]  # Test first 2 URLs
            content_data = service.get_content(urls)
            
            print(f"Retrieved content for {len(content_data)} URLs")
            for i, content in enumerate(content_data):
                print(f"\nContent {i+1}:")
                text = content.get('text', '')
                if text:
                    print(f"Length: {len(text)} characters")
                    print(f"Preview: {text[:500]}...")
                else:
                    print("No text content")
        
        return True
        
    except Exception as e:
        print(f"Error testing Exa content: {e}")
        return False

if __name__ == "__main__":
    test_exa_content_quality() 