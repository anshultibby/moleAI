"""
Test Zyte API Product Extractor

Run this to test Zyte API integration:
    python test_zyte_extractor.py
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

from app.modules.extractors.zyte_extractor import extract_products_from_url_zyte


async def test_zyte_extractor():
    """Test Zyte extractor with a few different sites"""
    
    test_sites = [
        {
            "name": "Hello Molly",
            "url": "https://www.hellomolly.com/collections/dresses",
            "description": "Known to have bot detection issues"
        },
        {
            "name": "ABC Fashion",
            "url": "https://www.abcfashion.com.au/collections/new-arrivals",
            "description": "Australian e-commerce site"
        },
    ]
    
    logger.info("=" * 80)
    logger.info("Testing Zyte API Product Extractor")
    logger.info("=" * 80)
    
    results = {}
    
    for site in test_sites:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing: {site['name']}")
        logger.info(f"URL: {site['url']}")
        logger.info(f"Description: {site['description']}")
        logger.info(f"{'='*80}\n")
        
        # Test manual extraction (default)
        logger.info("🔍 Method 1: Manual extraction (Zyte for HTML fetching)")
        result = await extract_products_from_url_zyte(
            site['url'],
            max_products=5,  # Limit to 5 for testing
            use_automatic=False
        )
        
        results[f"{site['name']} - Manual"] = result
        
        if result.get('success'):
            logger.info(f"✅ SUCCESS: Extracted {len(result['products'])} products")
            logger.info(f"   Meta: {json.dumps(result.get('meta', {}), indent=2)}")
            
            # Show first product as example
            if result['products']:
                first_product = result['products'][0]
                logger.info(f"\n   Example Product:")
                logger.info(f"   - Name: {first_product.get('product_name', 'N/A')}")
                logger.info(f"   - Price: {first_product.get('price', 'N/A')} {first_product.get('currency', '')}")
                logger.info(f"   - URL: {first_product.get('product_url', 'N/A')}")
                logger.info(f"   - Image: {first_product.get('image_url', 'N/A')[:80]}...")
        else:
            logger.error(f"❌ FAILED: {result.get('error', 'Unknown error')}")
        
        # Test automatic extraction
        logger.info("\n🤖 Method 2: Automatic extraction (Zyte AI)")
        result_auto = await extract_products_from_url_zyte(
            site['url'],
            max_products=5,
            use_automatic=True
        )
        
        results[f"{site['name']} - Automatic"] = result_auto
        
        if result_auto.get('success'):
            logger.info(f"✅ SUCCESS: Extracted {len(result_auto['products'])} products")
            if result_auto['products']:
                first_product = result_auto['products'][0]
                logger.info(f"\n   Example Product:")
                logger.info(f"   - Name: {first_product.get('product_name', 'N/A')}")
                logger.info(f"   - Price: {first_product.get('price', 'N/A')} {first_product.get('currency', '')}")
        else:
            logger.error(f"❌ FAILED: {result_auto.get('error', 'Unknown error')}")
        
        logger.info("\n" + "="*80 + "\n")
    
    # Save results
    output_file = "zyte_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n✅ Test results saved to: {output_file}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    
    for name, result in results.items():
        status = "✅ SUCCESS" if result.get('success') else "❌ FAILED"
        count = len(result.get('products', []))
        logger.info(f"{name}: {status} - {count} products")
    
    logger.info("="*80)


async def test_single_site(url: str, max_products: int = 10):
    """Test a single site"""
    logger.info(f"Testing: {url}")
    
    result = await extract_products_from_url_zyte(
        url,
        max_products=max_products,
        use_automatic=False
    )
    
    if result.get('success'):
        logger.info(f"✅ Extracted {len(result['products'])} products")
        
        # Display all products
        for i, product in enumerate(result['products'], 1):
            logger.info(f"\nProduct {i}:")
            logger.info(f"  Name: {product.get('product_name', 'N/A')}")
            logger.info(f"  Price: {product.get('price', 'N/A')} {product.get('currency', '')}")
            logger.info(f"  URL: {product.get('product_url', 'N/A')}")
            logger.info(f"  Image: {product.get('image_url', 'N/A')}")
    else:
        logger.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test a specific URL
        url = sys.argv[1]
        max_products = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        asyncio.run(test_single_site(url, max_products))
    else:
        # Run full test suite
        asyncio.run(test_zyte_extractor())
