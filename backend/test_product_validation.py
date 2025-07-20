#!/usr/bin/env python3
"""
Test product validation to ensure we don't return products with broken links
"""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

from app.utils.shopify_json_service import ShopifyJSONService

def test_product_validation():
    """Test product validation catches invalid products"""
    
    print("🧪 Testing Product Validation")
    print("=" * 50)
    
    service = ShopifyJSONService()
    
    # Test cases: good and bad products
    test_products = [
        {
            'title': 'Classic Blue Denim Jacket',
            'handle': 'classic-blue-denim-jacket',
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [{'available': True, 'price': '89.99'}],
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'body_html': '<p>A classic denim jacket</p>',
            'expected': True,
            'reason': 'Valid product with all required fields'
        },
        {
            'title': '',  # Missing title
            'handle': 'empty-title-product',
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [{'available': True, 'price': '89.99'}],
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'expected': False,
            'reason': 'Missing title'
        },
        {
            'title': 'Product With No Handle',
            'handle': '',  # Missing handle
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [{'available': True, 'price': '89.99'}],
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'expected': False,
            'reason': 'Missing handle'
        },
        {
            'title': 'Unpublished Product',
            'handle': 'unpublished-product',
            'published_at': None,  # Not published
            'variants': [{'available': True, 'price': '89.99'}],
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'expected': False,
            'reason': 'Not published'
        },
        {
            'title': 'Out of Stock Product',
            'handle': 'out-of-stock-product',
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [{'available': False, 'price': '89.99'}],  # Not available
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'expected': False,
            'reason': 'No available variants'
        },
        {
            'title': 'Product With No Variants',
            'handle': 'no-variants-product',
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [],  # No variants
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'expected': False,
            'reason': 'No variants'
        },
        {
            'title': 'Product With Bad Handle',
            'handle': 'bad handle with spaces',  # Invalid handle
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [{'available': True, 'price': '89.99'}],
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'expected': False,
            'reason': 'Invalid handle with spaces'
        },
        {
            'title': 'Product With Special Characters',
            'handle': 'product&with?special#chars',  # Invalid handle
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [{'available': True, 'price': '89.99'}],
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'expected': False,
            'reason': 'Invalid handle with special characters'
        },
        {
            'title': 'Product With No Images or Description',
            'handle': 'no-content-product',
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [{'available': True, 'price': '89.99'}],
            'images': [],  # No images
            'body_html': '',  # No description
            'expected': False,
            'reason': 'No images or description'
        },
        {
            'title': 'Valid Product With Dashes',
            'handle': 'valid-product-with-dashes',
            'published_at': '2024-01-15T10:00:00Z',
            'variants': [{'available': True, 'price': '89.99'}],
            'images': [{'src': 'https://example.com/jacket.jpg'}],
            'body_html': '<p>Good product</p>',
            'expected': True,
            'reason': 'Valid product with proper dashes in handle'
        }
    ]
    
    print(f"Testing {len(test_products)} product validation cases...\n")
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_products, 1):
        product = {k: v for k, v in test_case.items() if k not in ['expected', 'reason']}
        expected = test_case['expected']
        reason = test_case['reason']
        
        result = service._is_valid_product(product)
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{i:2}. {status} - {reason}")
        print(f"    Title: '{product.get('title', 'N/A')}'")
        print(f"    Handle: '{product.get('handle', 'N/A')}'")
        print(f"    Expected: {expected}, Got: {result}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"    ❌ Test failed! Expected {expected} but got {result}")
        
        print()
    
    # Test URL building
    print("🔗 Testing URL Building:")
    print("-" * 30)
    
    test_urls = [
        ('https://example-store.com', 'valid-product-handle', 'https://example-store.com/products/valid-product-handle'),
        ('https://shop.example.com/', 'another-product', 'https://shop.example.com/products/another-product'),
        ('', 'valid-handle', ''),  # Empty store URL
        ('https://store.com', '', ''),  # Empty handle
    ]
    
    for store_url, handle, expected_url in test_urls:
        result_url = service._build_validated_product_url(store_url, handle)
        status = "✅" if result_url == expected_url else "❌"
        print(f"{status} Store: '{store_url}' + Handle: '{handle}' → '{result_url}'")
        if result_url != expected_url:
            print(f"    Expected: '{expected_url}'")
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Success Rate: {passed}/{passed+failed} ({100*passed/(passed+failed):.1f}%)")
    
    if failed == 0:
        print(f"\n🎉 All validation tests passed! Product validation is working correctly.")
    else:
        print(f"\n⚠️  Some tests failed. Check the validation logic.")

if __name__ == "__main__":
    test_product_validation() 