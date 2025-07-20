#!/usr/bin/env python3
"""
Test domain filtering to ensure localhost and fake domains are blocked
"""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

from app.utils.shopify_json_service import ShopifyJSONService, search_multiple_stores

def test_domain_filtering():
    """Test that localhost and fake domains are properly filtered"""
    
    print("🧪 Testing Domain Filtering")
    print("=" * 50)
    
    service = ShopifyJSONService()
    
    # Test individual domain validation
    test_domains = [
        # Valid domains
        ("shop.gymshark.com", True, "Valid Shopify store"),
        ("example.myshopify.com", True, "Valid MyShopify domain"),
        ("store.nike.com", True, "Valid custom domain"),
        
        # Invalid domains - localhost
        ("localhost", False, "Localhost domain"),
        ("localhost:3000", False, "Localhost with port"),
        ("http://localhost:3000", False, "Localhost with protocol and port"),
        ("127.0.0.1", False, "IP localhost"),
        ("127.0.0.1:8080", False, "IP localhost with port"),
        
        # Invalid domains - fake/test
        ("example.com", False, "Example.com fake domain"),
        ("test.com", False, "Test.com fake domain"),
        ("fake.com", False, "Fake.com domain"),
        ("demo.com", False, "Demo.com domain"),
        
        # Edge cases
        ("", False, "Empty domain"),
        ("invalid", False, "Domain without dot"),
    ]
    
    print("Testing individual domain validation:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for domain, expected, description in test_domains:
        result = service._is_valid_domain(domain)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"{status} - {description}")
        print(f"   Domain: '{domain}'")
        print(f"   Expected: {expected}, Got: {result}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        print()
    
    # Test search function filtering
    print("Testing search function filtering:")
    print("-" * 50)
    
    test_searches = [
        ("shop.gymshark.com", "Should search normally"),
        ("localhost:3000", "Should be filtered out and return empty"),
        ("example.com", "Should be filtered out and return empty"),
    ]
    
    for domain, description in test_searches:
        print(f"Testing search for domain: '{domain}' - {description}")
        try:
            # This should either return products or an empty list, but not crash
            products = service.search_store_products(domain, "test query", limit=5)
            
            if not service._is_valid_domain(domain):
                # If domain is invalid, should return empty list
                if products == []:
                    print(f"   ✅ PASS: Invalid domain correctly returned empty list")
                    passed += 1
                else:
                    print(f"   ❌ FAIL: Invalid domain returned {len(products)} products")
                    failed += 1
            else:
                # If domain is valid, might return products or empty (depending on actual availability)
                print(f"   ✅ PASS: Valid domain processed (returned {len(products)} products)")
                passed += 1
                
        except Exception as e:
            print(f"   ❌ FAIL: Search raised exception: {e}")
            failed += 1
        print()
    
    # Test multiple store search filtering
    print("Testing multiple store search filtering:")
    print("-" * 50)
    
    mixed_domains = [
        "shop.gymshark.com",      # Valid
        "localhost:3000",         # Invalid - localhost
        "example.com",            # Invalid - fake domain
        "another-store.myshopify.com",  # Valid
        "127.0.0.1:8080",         # Invalid - localhost IP
    ]
    
    print(f"Testing with mixed domain list: {mixed_domains}")
    try:
        products = search_multiple_stores(mixed_domains, "test query", max_results=10)
        
        # Should only search valid domains
        print(f"   Result: {len(products)} products returned")
        print(f"   ✅ PASS: Multiple store search handled mixed domains")
        passed += 1
        
    except Exception as e:
        print(f"   ❌ FAIL: Multiple store search raised exception: {e}")
        failed += 1
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Success Rate: {passed}/{passed+failed} ({100*passed/(passed+failed):.1f}%)")
    
    if failed == 0:
        print(f"\n🎉 All domain filtering tests passed!")
        print(f"   ✅ Localhost domains are blocked")
        print(f"   ✅ Fake domains are blocked") 
        print(f"   ✅ Valid domains are allowed")
        print(f"   ✅ Search functions handle invalid domains gracefully")
    else:
        print(f"\n⚠️  Some tests failed. Domain filtering needs improvement.")

if __name__ == "__main__":
    test_domain_filtering() 