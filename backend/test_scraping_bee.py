#!/usr/bin/env python3
"""
Quick test script for ScrapingBee scraper
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from app.modules.scraping_bee import scrape_url, ScrapingBeeError

def test_scraping_bee():
    """Test ScrapingBee scraper with a simple URL"""
    
    # Test URLs - mix of static and JS-heavy sites
    test_urls = [
        "https://httpbin.org/html",  # Simple static HTML
        "https://quotes.toscrape.com/js/",  # JavaScript-rendered content
        "https://example.com"  # Basic static site
    ]
    
    print("Testing ScrapingBee scraper...")
    print("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nTest {i}: {url}")
        print("-" * 30)
        
        try:
            # Test without JavaScript rendering (faster, cheaper)
            print("Testing without JS rendering...")
            resource_no_js = scrape_url(url, render_js=False, wait=500)
            print(f"✓ Success (no JS): {len(resource_no_js.content)} characters")
            print(f"  Credits used: {resource_no_js.metadata.extra.get('credits_used', 'unknown')}")
            
            # Test with JavaScript rendering
            print("Testing with JS rendering...")
            resource_js = scrape_url(url, render_js=True, wait=2000)
            print(f"✓ Success (with JS): {len(resource_js.content)} characters")
            print(f"  Credits used: {resource_js.metadata.extra.get('credits_used', 'unknown')}")
            
            # Compare content lengths
            js_diff = len(resource_js.content) - len(resource_no_js.content)
            if js_diff > 0:
                print(f"  JS rendered {js_diff} additional characters")
            else:
                print(f"  No additional content from JS rendering")
                
        except ScrapingBeeError as e:
            print(f"✗ ScrapingBee error: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("SCRAPING_BEE_API_KEY"):
        print("❌ SCRAPING_BEE_API_KEY not found in environment variables")
        print("Please add your ScrapingBee API key to your .env file or environment")
        sys.exit(1)
    
    test_scraping_bee()
