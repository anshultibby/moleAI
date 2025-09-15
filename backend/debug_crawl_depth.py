#!/usr/bin/env python3
"""
Debug crawl depth and product page extraction
"""

import asyncio
from app.modules.product_extractor import ProductExtractor

async def debug_crawl_depth():
    """Debug why product pages aren't being processed"""
    
    extractor = ProductExtractor()
    
    # Test with a single ABC Fashion URL with more verbose logging
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    
    print(f"🔍 DEBUGGING CRAWL DEPTH")
    print(f"URL: {url}")
    print(f"MAX_DEPTH: {extractor.MAX_DEPTH}")
    print(f"={'='*80}")
    
    # Test with limited pages but higher depth
    products = await extractor.extract_from_url_and_links(url, max_links=3)
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Products found: {len(products)}")
    
    if products:
        for i, product in enumerate(products[:3], 1):
            print(f"\nProduct {i}:")
            print(f"  Name: {product.name}")
            print(f"  Price: ${product.get_price()} {product.get_currency()}")
            print(f"  Brand: {product.get_brand_name()}")
            print(f"  URL: {product.url}")
    else:
        print("❌ No products found")
        
        # Let's manually test one of the product URLs we know works
        print(f"\n🧪 MANUAL TEST OF KNOWN WORKING PRODUCT URL:")
        test_product_url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/products/applique-fitted-short-sleeve-gown-by-amelia-couture-7707"
        
        # Test direct extraction
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(test_product_url, headers={
                "User-Agent": "ProductExtractorBot/1.0 (+mailto:test@example.com)"
            }) as response:
                html = await response.text(errors="ignore")
                
                products = extractor._extract_products_from_html(html, test_product_url)
                print(f"Direct extraction from {test_product_url}: {len(products)} products")
                
                if products:
                    product = products[0]
                    print(f"  Name: {product.get('name')}")
                    print(f"  Price: {product.get('price')}")
                    print(f"  Brand: {product.get('brand')}")

if __name__ == "__main__":
    asyncio.run(debug_crawl_depth())
