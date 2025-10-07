#!/usr/bin/env python3
"""
Test script for Simple Product Extractor

Tests the 3-step heuristic:
1. Get HTML from URL
2. Find product links (href with 'product' in URL)
3. Extract JSON-LD from each product page
"""

import asyncio
import json
from loguru import logger

# Add the backend directory to the path
import sys
sys.path.append('/Users/anshul/code/moleAI/backend')

from app.modules.extractors.simple_extractor import extract_products_simple


async def test_simple_extraction():
    """Test simple extraction on real e-commerce sites"""
    
    # Test URLs - sites that likely have product links and JSON-LD
    test_urls = [
        "https://shop.mango.com/us/women/dresses",
        "https://www.zara.com/us/en/woman/dresses-l1066.html",
        "https://www2.hm.com/en_us/women/products/dresses.html"
    ]
    
    for url in test_urls:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {url}")
        logger.info(f"{'='*60}")
        
        try:
            result = await extract_products_simple(url, max_products=10)
            
            if result['success']:
                products = result['products']
                meta = result['meta']
                
                logger.info(f"✅ Success!")
                logger.info(f"Links found: {meta['total_links_found']}")
                logger.info(f"Products extracted: {meta['products_extracted']}")
                logger.info(f"Success rate: {meta['success_rate']:.2%}")
                
                # Show sample products
                logger.info("\nSample products:")
                for i, product in enumerate(products[:3], 1):
                    title = product.get('title', 'No title')[:50]
                    price = product.get('price', 'No price')
                    brand = product.get('brand', 'No brand')
                    logger.info(f"  {i}. {title}")
                    logger.info(f"     Brand: {brand}")
                    logger.info(f"     Price: {price}")
                    logger.info(f"     URL: {product.get('product_url', 'No URL')}")
                
                if len(products) > 3:
                    logger.info(f"  ... and {len(products) - 3} more products")
                
                # Show full result for first URL only
                if url == test_urls[0]:
                    print(f"\nFull result sample:")
                    print(json.dumps({
                        "success": result['success'],
                        "products": products[:1],  # Just first product
                        "meta": meta
                    }, indent=2))
                
            else:
                logger.error(f"❌ Failed: {result['error']}")
        
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
        
        # Pause between requests
        await asyncio.sleep(2)


async def test_step_by_step():
    """Test each step individually to see what's happening"""
    
    logger.info(f"\n{'='*60}")
    logger.info("Step-by-Step Test")
    logger.info(f"{'='*60}")
    
    url = "https://shop.mango.com/us/women/coats"
    
    try:
        from app.modules.extractors.simple_extractor import (
            get_html, find_product_links, extract_json_ld, extract_product_from_json_ld
        )
        
        # Step 1: Get HTML
        logger.info("Step 1: Getting HTML...")
        html = get_html(url)
        if html:
            logger.info(f"✅ Got {len(html)} characters of HTML")
        else:
            logger.error("❌ Failed to get HTML")
            return
        
        # Step 2: Find product links
        logger.info("Step 2: Finding product links...")
        product_links = find_product_links(html, url)
        logger.info(f"✅ Found {len(product_links)} product links")
        
        # Show first few links
        for i, link in enumerate(product_links[:5], 1):
            logger.info(f"  {i}. {link}")
        
        if len(product_links) > 5:
            logger.info(f"  ... and {len(product_links) - 5} more links")
        
        # Step 3: Test JSON-LD extraction on first product
        if product_links:
            logger.info("Step 3: Testing JSON-LD extraction on first product...")
            first_product_url = product_links[0]
            product_html = get_html(first_product_url)
            
            if product_html:
                json_ld_data = extract_json_ld(product_html)
                logger.info(f"✅ Found {len(json_ld_data)} JSON-LD items")
                
                product = extract_product_from_json_ld(json_ld_data)
                if product:
                    logger.info(f"✅ Extracted product: {product.get('title', 'Unknown')}")
                    print(f"\nSample product:")
                    print(json.dumps(product, indent=2))
                else:
                    logger.warning("❌ No product found in JSON-LD")
            else:
                logger.error("❌ Failed to get product page HTML")
        
    except Exception as e:
        logger.error(f"❌ Step-by-step test failed: {e}")


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Simple Extractor Tests")
    
    # Test 1: Step by step analysis
    await test_step_by_step()
    
    # Test 2: Full extraction workflow
    await test_simple_extraction()
    
    logger.info("\n🎉 All tests completed!")
    logger.info("\n💡 Simple approach:")
    logger.info("1. ✅ Get HTML from listing page")
    logger.info("2. ✅ Find links with 'product' in URL")
    logger.info("3. ✅ Extract JSON-LD from each product page")
    logger.info("\nClean, simple, and effective!")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())
