#!/usr/bin/env python3
"""Test the fixed simple extractor"""

import asyncio
import json
import sys
sys.path.append('/Users/anshul/code/moleAI/backend')

from app.modules.extractors.simple_extractor import extract_products_simple
from loguru import logger


async def test():
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    
    logger.info(f"Testing SIMPLE extractor with: {url}\n")
    
    result = await extract_products_simple(url, max_products=10)
    
    if result['success']:
        products = result['products']
        meta = result['meta']
        
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS!")
        print(f"{'='*80}")
        print(f"Total links found: {meta['total_links_found']}")
        print(f"Products extracted: {meta['products_extracted']}")
        print(f"Success rate: {meta['success_rate']:.2%}")
        print(f"{'='*80}\n")
        
        for i, product in enumerate(products, 1):
            print(f"\n🛍️  Product {i}:")
            print(f"  Name: {product.get('title', 'N/A')[:60]}")
            print(f"  Price: ${product.get('price', 'N/A')} {product.get('currency', '')}")
            print(f"  Brand: {product.get('brand', 'N/A')}")
            print(f"  SKU: {product.get('sku', 'N/A')}")
            print(f"  URL: {product.get('product_url', 'N/A')}")
        
        print(f"\n{'='*80}")
        print("✅ SIMPLE AND DUMB APPROACH WORKS!")
        print(f"{'='*80}")
        
    else:
        print(f"❌ Failed: {result['error']}")


if __name__ == "__main__":
    asyncio.run(test())

