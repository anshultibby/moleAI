#!/usr/bin/env python3
"""
Test script to demonstrate the optimized direct scraper performance
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from app.modules.direct_scraper import scrape_url, scrape_multiple_urls

def test_optimized_scraper():
    """Test the optimized scraper with various scenarios"""
    
    # Test URLs - mix of static and JS-heavy sites
    test_urls = [
        "https://httpbin.org/html",  # Simple static HTML
        "https://example.com",  # Basic static site
        "https://quotes.toscrape.com/",  # Static quotes site
        "https://quotes.toscrape.com/js/",  # JavaScript-rendered content
        "https://httpbin.org/json",  # JSON response (should be fast)
    ]
    
    print("🚀 Testing Optimized Direct Scraper")
    print("=" * 60)
    
    # Test 1: Single URL scraping with smart JS detection
    print("\n📄 Test 1: Single URL scraping with smart JS detection")
    print("-" * 40)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{i}. Testing: {url}")
        
        start_time = time.time()
        try:
            resource = scrape_url(
                url, 
                render_js=True,  # Allow JS but use smart detection
                wait=1000,
                smart_js_detection=True
            )
            
            elapsed = time.time() - start_time
            js_used = resource.metadata.extra.get('render_js', False)
            scrape_time = resource.metadata.extra.get('scrape_time_seconds', elapsed)
            
            print(f"   ✅ Success: {len(resource.content)} chars in {scrape_time:.2f}s")
            print(f"   🧠 JS rendering: {'Yes' if js_used else 'No (smart detection)'}")
            print(f"   ⚡ Speed: {'Fast' if scrape_time < 2 else 'Slow' if scrape_time > 5 else 'Medium'}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Test 2: Concurrent scraping
    print(f"\n🔄 Test 2: Concurrent scraping of {len(test_urls)} URLs")
    print("-" * 40)
    
    start_time = time.time()
    try:
        resources = scrape_multiple_urls(
            test_urls,
            render_js=True,
            wait=1000,
            max_workers=3,  # Use 3 workers for better performance
            smart_js_detection=True
        )
        
        total_time = time.time() - start_time
        successful = sum(1 for r in resources if len(r.content) > 0)
        js_used_count = sum(1 for r in resources if r.metadata.extra.get('render_js', False))
        
        print(f"   ✅ Completed: {successful}/{len(test_urls)} URLs in {total_time:.2f}s")
        print(f"   🧠 JS rendering used: {js_used_count}/{len(test_urls)} URLs")
        print(f"   ⚡ Average time per URL: {total_time/len(test_urls):.2f}s")
        print(f"   🚀 Performance: {'Excellent' if total_time < 5 else 'Good' if total_time < 10 else 'Needs improvement'}")
        
        # Show details for each URL
        for i, (url, resource) in enumerate(zip(test_urls, resources), 1):
            js_used = resource.metadata.extra.get('render_js', False)
            scrape_time = resource.metadata.extra.get('scrape_time_seconds', 0)
            status = "✅" if len(resource.content) > 0 else "❌"
            
            print(f"     {i}. {status} {url[:50]}... ({scrape_time:.2f}s, JS: {js_used})")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Compare with and without smart detection
    print(f"\n🧪 Test 3: Smart detection comparison")
    print("-" * 40)
    
    test_url = "https://httpbin.org/html"  # Known static site
    
    # Without smart detection (force JS)
    print(f"Testing {test_url} without smart detection (force JS)...")
    start_time = time.time()
    try:
        resource_force_js = scrape_url(
            test_url,
            render_js=True,
            smart_js_detection=False  # Force JS rendering
        )
        time_force_js = time.time() - start_time
        print(f"   Force JS: {time_force_js:.2f}s, {len(resource_force_js.content)} chars")
    except Exception as e:
        print(f"   Force JS failed: {e}")
        time_force_js = float('inf')
    
    # With smart detection
    print(f"Testing {test_url} with smart detection...")
    start_time = time.time()
    try:
        resource_smart = scrape_url(
            test_url,
            render_js=True,
            smart_js_detection=True  # Use smart detection
        )
        time_smart = time.time() - start_time
        js_used = resource_smart.metadata.extra.get('render_js', False)
        print(f"   Smart detection: {time_smart:.2f}s, {len(resource_smart.content)} chars, JS: {js_used}")
        
        if time_force_js != float('inf'):
            speedup = time_force_js / time_smart if time_smart > 0 else float('inf')
            print(f"   🚀 Speedup: {speedup:.1f}x faster with smart detection!")
            
    except Exception as e:
        print(f"   Smart detection failed: {e}")
    
    print("\n" + "=" * 60)
    print("✨ Optimization Summary:")
    print("   • Smart JS detection avoids unnecessary rendering")
    print("   • Playwright is faster and more reliable than requests-html")
    print("   • Concurrent processing speeds up multiple URLs")
    print("   • Resource blocking reduces load times")
    print("   • Intelligent waiting strategies minimize delays")
    print("=" * 60)

if __name__ == "__main__":
    test_optimized_scraper()
