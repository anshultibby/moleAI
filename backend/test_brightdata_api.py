"""
Test BrightData Web Unlocker API Product Extractor

This is the CHEAPEST BrightData option: $1.50 per 1000 requests

Run this to test:
    python test_brightdata_api.py "https://site.com/products" 5
"""

import asyncio
import json
import sys
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Add backend directory to path
sys.path.insert(0, '.')

from app.modules.extractors.brightdata_api_extractor import extract_products_from_url_brightdata_api


async def test_single_site(url: str, max_products: int = 10):
    """Test a single site"""
    logger.info(f"Testing BrightData Web Unlocker API with: {url}")
    logger.info("Cost: $1.50 per 1,000 requests (cheapest option!)")
    logger.info("=" * 80)
    
    result = await extract_products_from_url_brightdata_api(
        url,
        max_products=max_products
    )
    
    if result.get('success'):
        logger.info(f"✅ SUCCESS: Extracted {len(result['products'])} products")
        logger.info(f"\nMeta: {json.dumps(result.get('meta', {}), indent=2)}")
        
        # Display all products
        for i, product in enumerate(result['products'], 1):
            logger.info(f"\nProduct {i}:")
            logger.info(f"  Name: {product.get('product_name', 'N/A')}")
            logger.info(f"  Price: {product.get('price', 'N/A')} {product.get('currency', '')}")
            logger.info(f"  URL: {product.get('product_url', 'N/A')}")
            logger.info(f"  Image: {product.get('image_url', 'N/A')[:100]}...")
        
        # Calculate cost
        total_requests = 1 + len(result['products'])  # listing + products
        estimated_cost = total_requests * 0.0015  # $1.50 per 1000
        logger.info(f"\n💰 Estimated cost: ${estimated_cost:.4f} ({total_requests} requests)")
    else:
        logger.error(f"❌ FAILED: {result.get('error', 'Unknown error')}")
    
    logger.info("\n" + "=" * 80)
    return result


async def test_multiple_sites():
    """Test multiple sites"""
    test_sites = [
        {
            "name": "Hello Molly",
            "url": "https://www.hellomolly.com/collections/dresses",
            "max_products": 3
        },
        {
            "name": "Express.com",
            "url": "https://www.express.com/womens-clothing/dresses/cat550007",
            "max_products": 3
        }
    ]
    
    results = {}
    total_cost = 0
    
    for site in test_sites:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing: {site['name']}")
        logger.info(f"URL: {site['url']}")
        logger.info(f"{'='*80}\n")
        
        result = await extract_products_from_url_brightdata_api(
            site['url'],
            max_products=site['max_products']
        )
        
        results[site['name']] = result
        
        if result.get('success'):
            count = len(result['products'])
            logger.info(f"✅ SUCCESS: {count} products")
            
            # Calculate cost
            requests = 1 + count
            cost = requests * 0.0015
            total_cost += cost
            logger.info(f"   Cost: ${cost:.4f}")
            
            if result['products']:
                first = result['products'][0]
                logger.info(f"   Example: {first.get('product_name', 'N/A')} - ${first.get('price', 'N/A')}")
        else:
            logger.error(f"❌ FAILED: {result.get('error', 'Unknown')}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    
    for name, result in results.items():
        status = "✅ SUCCESS" if result.get('success') else "❌ FAILED"
        count = len(result.get('products', []))
        logger.info(f"{name}: {status} - {count} products")
    
    logger.info(f"\n💰 Total estimated cost: ${total_cost:.4f}")
    
    # Save results
    output_file = "brightdata_api_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"✅ Results saved to: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test a specific URL
        url = sys.argv[1]
        max_products = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        asyncio.run(test_single_site(url, max_products))
    else:
        # Run full test suite
        asyncio.run(test_multiple_sites())
