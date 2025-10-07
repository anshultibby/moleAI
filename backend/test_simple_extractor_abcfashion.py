#!/usr/bin/env python3
"""
Test Simple Product Extractor with ABC Fashion
"""

import asyncio
import json
import sys
sys.path.append('/Users/anshul/code/moleAI/backend')

from app.modules.extractors.simple_extractor import extract_products_simple
from loguru import logger


async def test_abc_fashion():
    """Test simple extraction on ABC Fashion"""
    
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing Simple Extractor with ABC Fashion")
    logger.info(f"URL: {url}")
    logger.info(f"{'='*80}\n")
    
    try:
        result = await extract_products_simple(url, max_products=10)
        
        if result['success']:
            products = result['products']
            meta = result['meta']
            
            logger.info(f"✅ SUCCESS!")
            logger.info(f"\nMeta Information:")
            logger.info(f"  Total links found: {meta['total_links_found']}")
            logger.info(f"  Products extracted: {meta['products_extracted']}")
            logger.info(f"  Success rate: {meta['success_rate']:.2%}")
            logger.info(f"  Strategy: {meta['strategy']}")
            
            # Show all products
            logger.info(f"\n{'='*80}")
            logger.info(f"EXTRACTED PRODUCTS ({len(products)} total)")
            logger.info(f"{'='*80}")
            
            for i, product in enumerate(products, 1):
                logger.info(f"\n🛍️  Product {i}:")
                logger.info(f"  📝 Title: {product.get('title', 'N/A')[:80]}")
                logger.info(f"  💰 Price: ${product.get('price', 'N/A')} {product.get('currency', '')}")
                logger.info(f"  🏷️  Brand: {product.get('brand', 'N/A')}")
                logger.info(f"  🔢 SKU: {product.get('sku', 'N/A')}")
                logger.info(f"  🔗 URL: {product.get('product_url', 'N/A')}")
            
            # Show full data for first product
            logger.info(f"\n{'='*80}")
            logger.info(f"SAMPLE PRODUCT (Full Data)")
            logger.info(f"{'='*80}")
            print(json.dumps(products[0], indent=2))
            
        else:
            logger.error(f"❌ FAILED: {result['error']}")
    
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_abc_fashion())

