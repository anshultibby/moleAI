"""
Test Jina AI Reader service
"""

from app.utils.jina_service import read_url_with_jina, read_urls_with_jina

def test_jina_single_url():
    """Test reading a single URL with Jina AI Reader"""
    print("Testing Jina AI Reader with single URL...")
    
    # Test with a known product page
    test_url = "https://www.target.com/p/sony-wh-ch720n-wireless-noise-canceling-over-ear-headphones/-/A-87002144"
    
    try:
        result = read_url_with_jina(test_url)
        
        if result and result.get('success'):
            print(f"✓ Successfully extracted content from {result.get('store_name', 'Unknown Store')}")
            print(f"Content length: {result.get('content_length', 0)} characters")
            print(f"Product name: {result.get('product_name', 'Not found')}")
            print(f"Price: {result.get('price', 'Not found')}")
            print(f"Brand: {result.get('brand', 'Not found')}")
            print(f"Availability: {result.get('availability', 'unknown')}")
            
            if result.get('images'):
                print(f"Images found: {len(result['images'])}")
            
            if result.get('content'):
                print(f"\nContent preview:")
                print("-" * 50)
                print(result['content'][:500] + "...")
                print("-" * 50)
            
            return True
        else:
            print(f"✗ Failed to extract content: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"Error testing Jina Reader: {e}")
        return False

def test_jina_multiple_urls():
    """Test reading multiple URLs with Jina AI Reader"""
    print("\n" + "="*60)
    print("Testing Jina AI Reader with multiple URLs...")
    
    test_urls = [
        "https://www.bestbuy.com/site/sony-wh-ch720n-wireless-noise-canceling-over-the-ear-headphones-black/6535195.p",
        "https://www.target.com/p/apple-airpods-3rd-generation/-/A-84671621"
    ]
    
    try:
        results = read_urls_with_jina(test_urls, max_workers=2)
        
        print(f"Processed {len(results)} URLs:")
        
        for i, result in enumerate(results, 1):
            print(f"\n--- RESULT {i} ---")
            print(f"URL: {result.get('url', 'N/A')}")
            print(f"Store: {result.get('store_name', 'N/A')}")
            print(f"Success: {result.get('success', False)}")
            
            if result.get('success'):
                print(f"Product: {result.get('product_name', 'N/A')}")
                print(f"Price: {result.get('price', 'N/A')}")
                print(f"Content length: {result.get('content_length', 0)} chars")
            else:
                print(f"Error: {result.get('error', 'Unknown')}")
        
        successful = sum(1 for r in results if r.get('success'))
        print(f"\nSuccess rate: {successful}/{len(results)} URLs")
        
        return successful > 0
        
    except Exception as e:
        print(f"Error testing multiple URLs: {e}")
        return False

def test_jina_amazon_page():
    """Test with an Amazon page (often challenging)"""
    print("\n" + "="*60)
    print("Testing Jina AI Reader with Amazon page...")
    
    amazon_url = "https://www.amazon.com/Sony-WH-1000XM4-Canceling-Headphones-Phone-Call/dp/B0863TXGM3"
    
    try:
        result = read_url_with_jina(amazon_url)
        
        if result and result.get('success'):
            print(f"✓ Successfully processed Amazon page!")
            print(f"Content length: {result.get('content_length', 0)} characters")
            print(f"Product name: {result.get('product_name', 'Not found')}")
            print(f"Price: {result.get('price', 'Not found')}")
            
            # Show a bit of the content
            if result.get('content'):
                content_preview = result['content'][:300]
                print(f"\nContent preview: {content_preview}...")
            
            return True
        else:
            print(f"✗ Failed with Amazon page: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"Error with Amazon test: {e}")
        return False

if __name__ == "__main__":
    print("Starting Jina AI Reader tests...")
    
    # Run tests
    single_success = test_jina_single_url()
    multiple_success = test_jina_multiple_urls()
    amazon_success = test_jina_amazon_page()
    
    print("\n" + "="*60)
    print("TEST RESULTS:")
    print(f"Single URL: {'PASS' if single_success else 'FAIL'}")
    print(f"Multiple URLs: {'PASS' if multiple_success else 'FAIL'}")
    print(f"Amazon page: {'PASS' if amazon_success else 'FAIL'}")
    
    if all([single_success, multiple_success, amazon_success]):
        print("\n🎉 All tests passed! Jina AI Reader is working great.")
    else:
        print("\n⚠️  Some tests failed, but Jina Reader may still be functional for most sites.") 