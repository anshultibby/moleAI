#!/usr/bin/env python3
"""
Test script to verify fixes work on previously failed sites
"""

import asyncio
import sys
from loguru import logger
from app.modules.product_extractor import ProductExtractor

async def test_failed_sites():
    """Test the previously failed sites with our fixes"""
    
    extractor = ProductExtractor()
    
    failed_sites = [
        {
            "name": "ABC Fashion",
            "url": "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black",
        },
        {
            "name": "The Dress Warehouse", 
            "url": "https://thedresswarehouse.com/collections/evening-dresses-under-100",
        },
        {
            "name": "Ever-Pretty (retest)",
            "url": "https://www.ever-pretty.com/collections/black-dresses?filter.v.option.color=Black",
        }
    ]
    
    for site in failed_sites:
        print(f"\n{'='*60}")
        print(f"🔍 TESTING: {site['name']}")
        print(f"URL: {site['url']}")
        print(f"{'='*60}")
        
        try:
            # Test with limited crawling to avoid overwhelming
            products = await extractor.extract_from_url_and_links(site['url'], max_links=5)
            
            print(f"✅ RESULT: Found {len(products)} products")
            
            if products:
                print(f"\n📦 SAMPLE PRODUCTS (first 3):")
                for i, product in enumerate(products[:3], 1):
                    print(f"\n  Product {i}:")
                    print(f"    Name: {product.name}")
                    print(f"    Price: ${product.get_price()} {product.get_currency()}")
                    print(f"    Brand: {product.get_brand_name()}")
                    print(f"    Description: {product.description}")
                    print(f"    URL: {product.url}")
                
                # Check for improvements
                has_prices = sum(1 for p in products if p.get_price() is not None)
                has_brands = sum(1 for p in products if p.get_brand_name() is not None)
                has_descriptions = sum(1 for p in products if p.description is not None)
                
                print(f"\n📊 QUALITY METRICS:")
                print(f"    Products with prices: {has_prices}/{len(products)} ({has_prices/len(products)*100:.1f}%)")
                print(f"    Products with brands: {has_brands}/{len(products)} ({has_brands/len(products)*100:.1f}%)")
                print(f"    Products with descriptions: {has_descriptions}/{len(products)} ({has_descriptions/len(products)*100:.1f}%)")
                
                if site['name'] == "ABC Fashion" and len(products) > 0:
                    print(f"🎉 SUCCESS: ABC Fashion extraction now working!")
                elif site['name'] == "The Dress Warehouse" and len(products) > 0:
                    print(f"🎉 SUCCESS: The Dress Warehouse extraction now working!")
                elif site['name'] == "Ever-Pretty (retest)":
                    if has_prices > 0:
                        print(f"🎉 SUCCESS: Ever-Pretty price extraction fixed!")
                    if has_descriptions > 0:
                        print(f"🎉 SUCCESS: Ever-Pretty description extraction improved!")
            else:
                print(f"⚠️ WARNING: No products found for {site['name']}")
                print(f"   This may indicate the site structure has changed or requires different selectors")
                
        except Exception as e:
            print(f"❌ ERROR: Failed to test {site['name']}: {e}")
            logger.exception(f"Full error for {site['name']}:")

    print(f"\n{'='*60}")
    print("🏁 TESTING COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(test_failed_sites())
