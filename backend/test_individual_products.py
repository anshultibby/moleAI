#!/usr/bin/env python3
"""
Test individual product pages to see why they're not extracting data
"""

import asyncio
import aiohttp
from app.modules.product_extractor import ProductExtractor

async def test_individual_product_pages():
    """Test individual product pages from the sites"""
    
    extractor = ProductExtractor()
    
    # Sample product URLs found from our investigation
    test_urls = [
        {
            "site": "ABC Fashion",
            "url": "https://www.abcfashion.net/collections/long-prom-dresses-under-100/products/applique-fitted-short-sleeve-gown-by-amelia-couture-7707"
        },
        {
            "site": "ABC Fashion", 
            "url": "https://www.abcfashion.net/collections/long-prom-dresses-under-100/products/velvet-fitted-strapless-slit-gown-by-amelia-couture-bz9029v"
        },
        {
            "site": "The Dress Warehouse",
            "url": "https://thedresswarehouse.com/collections/evening-dresses-under-100/products/mon-cheri-cp21246"
        },
        {
            "site": "The Dress Warehouse",
            "url": "https://thedresswarehouse.com/collections/evening-dresses-under-100/products/la-vera-14033"
        },
        {
            "site": "Amazon",
            "url": "https://www.amazon.com/FQA-Evening-Dresses-Elegant-Sleeveless/dp/B0BYSMYCR8"
        },
        {
            "site": "Amazon",
            "url": "https://www.amazon.com/Parthea-Wedding-Dresses-Sleeveless-Backless/dp/B0DRVDGCW8"
        }
    ]
    
    for test_case in test_urls:
        print(f"\n{'='*80}")
        print(f"🔍 TESTING INDIVIDUAL PRODUCT: {test_case['site']}")
        print(f"URL: {test_case['url']}")
        print(f"{'='*80}")
        
        try:
            # Test HTML extraction directly
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(test_case['url'], headers={
                    "User-Agent": "ProductExtractorBot/1.0 (+mailto:test@example.com)"
                }) as response:
                    html = await response.text(errors="ignore")
                    
                    print(f"✅ Page fetched: {len(html)} characters")
                    
                    # Test our extraction method directly
                    products = extractor._extract_products_from_html(html, test_case['url'])
                    print(f"✅ Raw extraction found: {len(products)} products")
                    
                    if products:
                        for i, product in enumerate(products, 1):
                            print(f"\n📦 Product {i}:")
                            print(f"  Name: {product.get('name', 'N/A')}")
                            print(f"  Price: {product.get('price', 'N/A')}")
                            print(f"  Currency: {product.get('priceCurrency', 'N/A')}")
                            print(f"  Brand: {product.get('brand', 'N/A')}")
                            print(f"  Description: {product.get('description', 'N/A')}")
                            print(f"  URL: {product.get('url', 'N/A')}")
                            
                            # Test schema conversion
                            try:
                                schema_product = extractor._convert_to_schema_org_product(product)
                                print(f"  ✅ Schema conversion successful")
                                print(f"    Schema Name: {schema_product.name}")
                                print(f"    Schema Price: ${schema_product.get_price()} {schema_product.get_currency()}")
                                print(f"    Schema Brand: {schema_product.get_brand_name()}")
                            except Exception as e:
                                print(f"  ❌ Schema conversion failed: {e}")
                    else:
                        print("❌ No products found in HTML")
                        
                        # Debug: Check for JSON-LD scripts
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, 'html.parser')
                        json_scripts = soup.find_all('script', type='application/ld+json')
                        print(f"🔍 JSON-LD scripts found: {len(json_scripts)}")
                        
                        for i, script in enumerate(json_scripts[:2]):
                            try:
                                import json
                                data = json.loads(script.string)
                                print(f"📋 JSON-LD Script {i+1}: {json.dumps(data, indent=2)[:500]}...")
                            except:
                                print(f"⚠️ Invalid JSON in script {i+1}")
                        
                        # Check for microdata
                        microdata_elements = soup.find_all(attrs={"itemtype": True})
                        print(f"🔍 Microdata elements: {len(microdata_elements)}")
                        
                        if microdata_elements:
                            for elem in microdata_elements[:3]:
                                print(f"  - {elem.get('itemtype')}: {elem.name}")
                        
        except Exception as e:
            print(f"❌ ERROR testing {test_case['site']}: {e}")

    print(f"\n{'='*80}")
    print("🏁 INDIVIDUAL PRODUCT TESTING COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_individual_product_pages())
