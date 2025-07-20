#!/usr/bin/env python3
"""
Test URL validation by making actual HTTP requests to check if product URLs work
"""

import os
import sys
import requests
from urllib.parse import urlparse

# Add the app directory to the path
sys.path.append('app')

from app.utils.shopify_json_service import ShopifyJSONService

def test_specific_url(url: str) -> dict:
    """Test a specific URL to see if it works"""
    print(f"🔍 Testing URL: {url}")
    
    result = {
        'url': url,
        'accessible': False,
        'status_code': None,
        'error': None,
        'redirect_url': None,
        'is_shopify': False
    }
    
    try:
        # Make a HEAD request first (faster than GET)
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        result['status_code'] = response.status_code
        result['accessible'] = response.status_code in [200, 301, 302]
        
        # Check if we were redirected
        if response.url != url:
            result['redirect_url'] = response.url
            print(f"   🔄 Redirected to: {response.url}")
        
        # Check if it's a Shopify store
        if 'shopify' in response.headers.get('server', '').lower() or \
           'myshopify.com' in response.url or \
           'cdn.shopify.com' in str(response.headers):
            result['is_shopify'] = True
        
        if result['accessible']:
            print(f"   ✅ SUCCESS: Status {response.status_code}")
            if result['is_shopify']:
                print(f"   🏪 Confirmed Shopify store")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
            
    except requests.exceptions.Timeout:
        result['error'] = 'Timeout'
        print(f"   ⏰ TIMEOUT: Server took too long to respond")
        
    except requests.exceptions.ConnectionError:
        result['error'] = 'Connection Error'
        print(f"   🔌 CONNECTION ERROR: Could not connect to server")
        
    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
        print(f"   ❌ REQUEST ERROR: {e}")
        
    return result

def test_url_construction():
    """Test how URLs are being constructed and if they work"""
    
    print("🧪 Testing URL Construction and Validation")
    print("=" * 60)
    
    # Test the specific broken URL mentioned
    test_url = "https://us.lovefitwear.com/products/black-high-impact-leggings"
    
    print("1. Testing the specific broken URL:")
    print("-" * 40)
    result = test_specific_url(test_url)
    
    # Parse the URL to understand its structure
    parsed = urlparse(test_url)
    print(f"\nURL Analysis:")
    print(f"   Domain: {parsed.netloc}")
    print(f"   Path: {parsed.path}")
    print(f"   Full URL: {test_url}")
    
    # Test if the domain itself is accessible
    print(f"\n2. Testing base domain accessibility:")
    print("-" * 40)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    base_result = test_specific_url(base_url)
    
    # Test if it's a valid Shopify store by checking products.json
    print(f"\n3. Testing Shopify products.json endpoint:")
    print("-" * 40)
    products_json_url = f"{base_url}/products.json"
    products_result = test_specific_url(products_json_url)
    
    # If products.json works, test if we can find the actual product
    if products_result['accessible']:
        print(f"\n4. Searching for the product in products.json:")
        print("-" * 40)
        
        try:
            response = requests.get(products_json_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                print(f"   📦 Found {len(products)} products in store")
                
                # Look for products with "black" and "legging" in title or handle
                matching_products = []
                for product in products:
                    title = product.get('title', '').lower()
                    handle = product.get('handle', '').lower()
                    if ('black' in title or 'black' in handle) and ('legging' in title or 'legging' in handle):
                        matching_products.append(product)
                
                print(f"   🎯 Found {len(matching_products)} products matching 'black leggings'")
                
                if matching_products:
                    print(f"   Products found:")
                    for i, product in enumerate(matching_products[:3], 1):  # Show first 3
                        title = product.get('title', 'Unknown')
                        handle = product.get('handle', 'unknown')
                        constructed_url = f"{base_url}/products/{handle}"
                        print(f"   {i}. {title}")
                        print(f"      Handle: {handle}")
                        print(f"      URL: {constructed_url}")
                        
                        # Test if this constructed URL works
                        if constructed_url == test_url:
                            print(f"      🎯 This matches our test URL!")
                        else:
                            print(f"      🔍 Testing constructed URL...")
                            test_result = test_specific_url(constructed_url)
                            
                else:
                    print(f"   ⚠️  No products found matching 'black leggings'")
                    print(f"   Available products (first 5):")
                    for i, product in enumerate(products[:5], 1):
                        print(f"   {i}. {product.get('title', 'Unknown')} (handle: {product.get('handle', 'unknown')})")
            else:
                print(f"   ❌ Failed to fetch products.json: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error fetching products: {e}")
    
    return {
        'test_url_result': result,
        'base_url_result': base_result,
        'products_json_result': products_result
    }

def test_shopify_service_url_building():
    """Test our Shopify service URL building with the problematic domain"""
    
    print(f"\n5. Testing ShopifyJSONService with this domain:")
    print("-" * 40)
    
    service = ShopifyJSONService()
    
    # Extract domain from the problematic URL
    test_domain = "us.lovefitwear.com"
    
    print(f"Testing domain: {test_domain}")
    
    # Test domain validation
    is_valid = service._is_valid_domain(test_domain)
    print(f"   Domain validation: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    if is_valid:
        # Test URL variants generation
        clean_domain = service._clean_domain(test_domain)
        url_variants = service._get_url_variants(clean_domain)
        
        print(f"   Cleaned domain: {clean_domain}")
        print(f"   URL variants generated:")
        for i, variant in enumerate(url_variants, 1):
            print(f"   {i}. {variant}")
            
            # Test if each variant works
            test_result = test_specific_url(variant + "/products.json")
            if test_result['accessible']:
                print(f"      ✅ This variant works!")
            else:
                print(f"      ❌ This variant doesn't work")
        
        # Test actual search
        print(f"\n   Testing actual product search:")
        try:
            products = service.search_store_products(test_domain, "black leggings", limit=5)
            print(f"   📦 Search returned {len(products)} products")
            
            if products:
                print(f"   Products found:")
                for i, product in enumerate(products, 1):
                    name = product.get('product_name', 'Unknown')
                    url = product.get('product_url', 'No URL')
                    print(f"   {i}. {name}")
                    print(f"      URL: {url}")
                    
                    # Test if this URL works
                    if url and url != 'No URL':
                        url_test = test_specific_url(url)
                        status = "✅ WORKS" if url_test['accessible'] else "❌ BROKEN"
                        print(f"      Status: {status}")
            else:
                print(f"   ⚠️  No products found")
                
        except Exception as e:
            print(f"   ❌ Search failed: {e}")

def main():
    """Run all URL validation tests"""
    
    print("🔗 Product URL Validation Test Suite")
    print("=" * 60)
    
    # Test the specific problematic URL
    results = test_url_construction()
    
    # Test our service's URL building
    test_shopify_service_url_building()
    
    # Summary
    print(f"\n📊 Summary:")
    print("-" * 20)
    
    test_url_accessible = results['test_url_result']['accessible']
    base_url_accessible = results['base_url_result']['accessible']
    products_json_accessible = results['products_json_result']['accessible']
    
    print(f"   Target URL accessible: {'✅' if test_url_accessible else '❌'}")
    print(f"   Base domain accessible: {'✅' if base_url_accessible else '❌'}")
    print(f"   Products.json accessible: {'✅' if products_json_accessible else '❌'}")
    
    if not test_url_accessible:
        if not base_url_accessible:
            print(f"\n🔍 Issue: The entire domain appears to be inaccessible")
        elif not products_json_accessible:
            print(f"\n🔍 Issue: Domain works but it's not a Shopify store")
        else:
            print(f"\n🔍 Issue: Store works but the specific product URL is broken")
    else:
        print(f"\n✅ All tests passed - URL should be working")

if __name__ == "__main__":
    main() 