#!/usr/bin/env python3
"""
Test URL classification logic
"""

from app.modules.product_extractor import ProductExtractor

def test_url_classification():
    """Test URL classification for our problem URLs"""
    
    extractor = ProductExtractor()
    
    test_urls = [
        "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black",
        "https://thedresswarehouse.com/collections/evening-dresses-under-100", 
        "https://www.amazon.com/Black-evening-dresses-50-100/s?rh=n%3A21308586011%2Cp_36%3A2661614011"
    ]
    
    print("🔍 TESTING URL CLASSIFICATION")
    print("="*60)
    
    for url in test_urls:
        classification = extractor._classify_url(url)
        print(f"URL: {url}")
        print(f"Classification: {classification}")
        
        # Check what patterns match
        url_lower = url.lower()
        patterns = ["/page/", "/category/", "/collection/", "/collections/", "/shop/", "/search", "/s?"]
        
        print("Pattern matches:")
        for pattern in patterns:
            if pattern in url_lower:
                print(f"  ✅ {pattern}")
            else:
                print(f"  ❌ {pattern}")
        
        # Check product hints
        import re
        product_hints_re = re.compile(r"/(product|p/|sku|item|dp/)", re.I)
        if product_hints_re.search(url):
            print("  ✅ Product hints match")
        else:
            print("  ❌ Product hints don't match")
        
        print("-" * 60)

if __name__ == "__main__":
    test_url_classification()
