#!/usr/bin/env python3
"""
Test ABC Fashion with debug logging
"""

import asyncio
import logging
from loguru import logger
from app.modules.product_extractor import ProductExtractor

async def test_abc_fashion_debug():
    """Test ABC Fashion with debug logging enabled"""
    
    # Enable debug logging
    logger.add("abc_debug.log", level="DEBUG", rotation="1 MB")
    
    extractor = ProductExtractor()
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    
    print(f"🔍 TESTING ABC FASHION WITH DEBUG LOGGING")
    print(f"URL: {url}")
    print(f"Check abc_debug.log for detailed logs")
    print(f"={'='*60}")
    
    # Test with very limited crawling
    products = await extractor.extract_from_url_and_links(url, max_links=2)
    
    print(f"\n📊 RESULTS:")
    print(f"Products found: {len(products)}")
    
    if products:
        for i, product in enumerate(products, 1):
            print(f"Product {i}: {product.name} - ${product.get_price()}")
    else:
        print("❌ No products found")
        print("Check abc_debug.log for details")

if __name__ == "__main__":
    asyncio.run(test_abc_fashion_debug())
