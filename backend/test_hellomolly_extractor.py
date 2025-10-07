"""
Test the updated simple extractor with Hello Molly
"""

import asyncio
import sys
import json
from loguru import logger

# Add the backend directory to the path
sys.path.insert(0, '/Users/anshul/code/moleAI/backend')

from app.modules.extractors.simple_extractor import extract_products_simple


async def main():
    url = "https://www.hellomolly.com/collections/formal/color_black"
    
    logger.info(f"Testing enhanced extractor with: {url}")
    
    result = await extract_products_simple(url, max_products=5)
    
    print("\n" + "="*80)
    print("EXTRACTION RESULTS")
    print("="*80)
    print(f"Success: {result.get('success')}")
    print(f"Error: {result.get('error', 'None')}")
    
    meta = result.get('meta', {})
    print(f"\nMetadata:")
    print(f"  - Used JS Rendering: {meta.get('used_js_rendering', 'N/A')}")
    print(f"  - HTML Length: {meta.get('html_length', 0):,} characters")
    print(f"  - Links Found: {meta.get('total_links_found', 0)}")
    print(f"  - Products Extracted: {meta.get('products_extracted', 0)}")
    print(f"  - Success Rate: {meta.get('success_rate', 0):.1%}")
    
    products = result.get('products', [])
    print(f"\nProducts ({len(products)}):")
    for i, product in enumerate(products[:3], 1):
        print(f"\n{i}. {product.get('title', 'Unknown')}")
        print(f"   Price: {product.get('price', 'N/A')} {product.get('currency', '')}")
        print(f"   Brand: {product.get('brand', 'N/A')}")
        print(f"   URL: {product.get('product_url', 'N/A')[:80]}...")
        if product.get('image_url'):
            print(f"   Image: {product.get('image_url')[:80]}...")
    
    # Save full results
    output_file = "hellomolly_extractor_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n📄 Full results saved to: {output_file}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

