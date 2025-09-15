#!/usr/bin/env python3
"""
Debug what products are found on collection pages
"""

import asyncio
import aiohttp
from app.modules.product_extractor import ProductExtractor

async def debug_collection_pages():
    """Debug what's happening on collection pages"""
    
    extractor = ProductExtractor()
    
    collection_urls = [
        "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black",
        "https://thedresswarehouse.com/collections/evening-dresses-under-100",
        "https://www.amazon.com/Black-evening-dresses-50-100/s?rh=n%3A21308586011%2Cp_36%3A2661614011"
    ]
    
    for url in collection_urls:
        print(f"\n{'='*80}")
        print(f"🔍 DEBUGGING COLLECTION PAGE")
        print(f"URL: {url}")
        print(f"{'='*80}")
        
        try:
            # Fetch the page
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={
                    "User-Agent": "ProductExtractorBot/1.0 (+mailto:test@example.com)"
                }) as response:
                    html = await response.text(errors="ignore")
                    
                    # Test what our extraction finds
                    products = extractor._extract_products_from_html(html, url)
                    print(f"✅ Products found on collection page: {len(products)}")
                    
                    if products:
                        print(f"📦 Collection page products:")
                        for i, product in enumerate(products, 1):
                            print(f"  Product {i}:")
                            print(f"    Name: {product.get('name', 'N/A')}")
                            print(f"    Type: {product.get('_raw', {}).get('@type', 'N/A')}")
                            print(f"    Price: {product.get('price', 'N/A')}")
                            print(f"    Brand: {product.get('brand', 'N/A')}")
                    
                    # Test page classification
                    page_type = extractor._classify_url(url)
                    print(f"✅ Page classified as: {page_type}")
                    
                    # Test product link extraction
                    product_links = extractor._extract_product_links_from_listing(html, url)
                    print(f"✅ Product links found: {len(product_links)}")
                    
                    # Show the logic condition
                    condition_result = page_type == "listing" and not products
                    print(f"✅ Condition 'listing and not products': {condition_result}")
                    print(f"   - page_type == 'listing': {page_type == 'listing'}")
                    print(f"   - not products: {not products}")
                    
                    if not condition_result:
                        print(f"❌ ISSUE FOUND: Product links won't be extracted because condition is False!")
                        print(f"   The collection page has {len(products)} products, so 'not products' is False")
                    else:
                        print(f"✅ Product links would be extracted")
                        
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_collection_pages())
