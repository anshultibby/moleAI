#!/usr/bin/env python3
"""
Test domain validation to ensure fake/test domains are filtered out
"""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

from app.utils.shopify_json_service import ShopifyJSONService
from app.utils.google_discovery_service import GoogleDiscoveryService

def test_domain_validation():
    """Test that fake/test domains are properly filtered out"""
    
    print("🧪 Testing Domain Validation")
    print("=" * 50)
    
    # Test Shopify JSON Service validation
    service = ShopifyJSONService()
    
    print("\n1️⃣ Testing Shopify JSON Service domain validation...")
    
    # Valid domains (should pass)
    valid_domains = [
        "gymshark.myshopify.com",
        "allbirds.myshopify.com", 
        "bombas.myshopify.com",
        "rains-dk.myshopify.com",
        "bosideng-fashion.myshopify.com"
    ]
    
    # Invalid domains (should be filtered out)
    invalid_domains = [
        "example.com",
        "test.myshopify.com",
        "demo.myshopify.com",
        "fake.com",
        "placeholder.com",
        "localhost",
        "127.0.0.1",
        "sample.myshopify.com"
    ]
    
    print("✅ Valid domains (should pass):")
    for domain in valid_domains:
        is_valid = service._is_valid_domain(domain)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"   {domain}: {status}")
    
    print("\n❌ Invalid domains (should be filtered out):")
    for domain in invalid_domains:
        is_valid = service._is_valid_domain(domain)
        status = "✅ FILTERED" if not is_valid else "❌ NOT FILTERED"
        print(f"   {domain}: {status}")
    
    # Test Google Discovery Service validation
    print(f"\n2️⃣ Testing Google Discovery Service domain validation...")
    
    try:
        discovery = GoogleDiscoveryService()
        
        # Test URL extraction with fake URLs
        test_urls = [
            "https://example.com/products/floral-print-maxi-dress",
            "https://test.myshopify.com/collections/dresses",
            "https://real-store.myshopify.com/products/jacket",
            "https://demo.myshopify.com/search",
            "https://awesome-fashion.myshopify.com/collections/winter"
        ]
        
        print("🔍 Testing URL extraction and validation:")
        for url in test_urls:
            extracted_domain = discovery._extract_shopify_domain(url)
            if extracted_domain:
                print(f"   ✅ ACCEPTED: {url} → {extracted_domain}")
            else:
                print(f"   ❌ FILTERED: {url}")
                
    except Exception as e:
        print(f"❌ Google Discovery test failed: {e}")
    
    # Test product search with invalid domains
    print(f"\n3️⃣ Testing product search with mixed domains...")
    
    mixed_domains = [
        "example.com",  # Should be filtered
        "rains-dk.myshopify.com",  # Should work
        "test.myshopify.com",  # Should be filtered
        "bosideng-fashion.myshopify.com"  # Should work
    ]
    
    all_products = []
    valid_stores_processed = []
    
    for domain in mixed_domains:
        print(f"🏪 Testing {domain}...")
        products = service.search_store_products(domain, "jacket", limit=5)
        
        if products:
            all_products.extend(products)
            valid_stores_processed.append(domain)
            print(f"   ✅ Got {len(products)} products")
        else:
            print(f"   ❌ No products (filtered or no results)")
    
    print(f"\n📊 Summary:")
    print(f"   🏪 Domains tested: {len(mixed_domains)}")
    print(f"   ✅ Valid domains processed: {len(valid_stores_processed)}")
    print(f"   📦 Total products found: {len(all_products)}")
    print(f"   🚫 Invalid domains filtered: {len(mixed_domains) - len(valid_stores_processed)}")
    
    # Check for any example.com URLs in results
    example_urls = [p for p in all_products if 'example.com' in p.get('product_url', '') or 'example.com' in p.get('image_url', '')]
    
    if example_urls:
        print(f"\n⚠️  WARNING: Found {len(example_urls)} products with example.com URLs!")
        for product in example_urls[:3]:
            print(f"   - {product.get('product_name', 'Unknown')}: {product.get('product_url', 'No URL')}")
    else:
        print(f"\n🎉 SUCCESS: No example.com URLs found in results!")

if __name__ == "__main__":
    test_domain_validation() 