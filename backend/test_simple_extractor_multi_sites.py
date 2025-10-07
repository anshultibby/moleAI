#!/usr/bin/env python3
"""
Test Simple Extractor on Multiple E-commerce Sites

Tests the simple 3-step approach on:
- Mango
- Zara
- Shein
- ABC Fashion
"""

import asyncio
import json
import sys
sys.path.append('/Users/anshul/code/moleAI/backend')

from app.modules.extractors.simple_extractor import extract_products_simple
from loguru import logger


async def test_site(site_name: str, url: str, max_products: int = 10):
    """Test extraction on a single site"""
    
    print(f"\n{'='*80}")
    print(f"🌐 TESTING: {site_name}")
    print(f"{'='*80}")
    print(f"URL: {url}")
    print(f"Max products: {max_products}\n")
    
    try:
        result = await extract_products_simple(url, max_products=max_products)
        
        if result['success']:
            products = result['products']
            meta = result['meta']
            
            print(f"✅ SUCCESS!")
            print(f"\nStats:")
            print(f"  Links found: {meta['total_links_found']}")
            print(f"  Products extracted: {meta['products_extracted']}")
            print(f"  Success rate: {meta['success_rate']:.2%}")
            
            if products:
                print(f"\nSample Products (first 3):")
                for i, product in enumerate(products[:3], 1):
                    title = product.get('title', 'No title')
                    price = product.get('price', 'N/A')
                    currency = product.get('currency', '')
                    brand = product.get('brand', 'No brand')
                    url = product.get('product_url', 'No URL')
                    
                    print(f"\n  {i}. {title[:60]}")
                    print(f"     Price: {price} {currency}")
                    print(f"     Brand: {brand}")
                    print(f"     URL: {url[:80]}...")
                
                if len(products) > 3:
                    print(f"\n  ... and {len(products) - 3} more products")
            else:
                print(f"\n⚠️  No products extracted (but links were found)")
                
            return {
                "site": site_name,
                "success": True,
                "links_found": meta['total_links_found'],
                "products_extracted": meta['products_extracted'],
                "success_rate": meta['success_rate']
            }
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            return {
                "site": site_name,
                "success": False,
                "error": result.get('error', 'Unknown error')
            }
    
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return {
            "site": site_name,
            "success": False,
            "error": str(e)
        }


async def main():
    """Test multiple e-commerce sites"""
    
    print(f"\n{'='*80}")
    print(f"🚀 SIMPLE EXTRACTOR - MULTI-SITE TEST")
    print(f"{'='*80}")
    print(f"\nTesting the simple 3-step approach:")
    print(f"1. Get HTML from listing page")
    print(f"2. Find product links in containers with 'product' text")
    print(f"3. Extract JSON-LD from each product page")
    print(f"{'='*80}\n")
    
    # Test sites with their collection/listing URLs
    test_sites = [
        {
            "name": "ABC Fashion",
            "url": "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black",
            "max_products": 10
        },
        {
            "name": "Mango",
            "url": "https://shop.mango.com/us/women/dresses-midi_d1b978be",
            "max_products": 10
        },
        {
            "name": "Zara",
            "url": "https://www.zara.com/us/en/woman-dresses-l1066.html",
            "max_products": 10
        },
        {
            "name": "Shein",
            "url": "https://us.shein.com/Women-Dresses-c-1727.html",
            "max_products": 10
        }
    ]
    
    results = []
    
    for site in test_sites:
        result = await test_site(
            site_name=site["name"],
            url=site["url"],
            max_products=site["max_products"]
        )
        results.append(result)
        
        # Small delay between sites to be polite
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"📊 SUMMARY")
    print(f"{'='*80}\n")
    
    for result in results:
        site = result['site']
        if result['success']:
            links = result.get('links_found', 0)
            products = result.get('products_extracted', 0)
            rate = result.get('success_rate', 0)
            print(f"✅ {site:20} - {products}/{links} products ({rate:.1%} success)")
        else:
            error = result.get('error', 'Unknown')
            print(f"❌ {site:20} - FAILED: {error[:50]}")
    
    # Save results
    with open('multi_site_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ Test complete! Results saved to: multi_site_test_results.json")
    print(f"{'='*80}\n")
    
    # Show what worked and what didn't
    successes = [r for r in results if r['success'] and r.get('products_extracted', 0) > 0]
    failures = [r for r in results if not r['success'] or r.get('products_extracted', 0) == 0]
    
    print(f"\n💡 Analysis:")
    print(f"  ✅ Working sites: {len(successes)}/{len(results)}")
    print(f"  ❌ Failed sites: {len(failures)}/{len(results)}")
    
    if successes:
        print(f"\n  Sites with successful extraction:")
        for r in successes:
            print(f"    - {r['site']}")
    
    if failures:
        print(f"\n  Sites that failed:")
        for r in failures:
            print(f"    - {r['site']}")


if __name__ == "__main__":
    asyncio.run(main())

