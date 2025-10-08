"""Quick test of Saboskirt with data-product-url fix"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.modules.extractors.brightdata_api_extractor import extract_products_brightdata_api


async def main():
    print("\n" + "="*80)
    print("🧪 TESTING SABOSKIRT WITH data-product-url FIX")
    print("="*80 + "\n")
    
    url = "https://us.saboskirt.com/collections/dresses/maxi-dresses"
    
    result = await extract_products_brightdata_api(url, max_products=10, timeout=60)
    
    if result['success']:
        products = result.get('products', [])
        strategy = result.get('meta', {}).get('strategy', 'unknown')
        fast_path = 'html_grid' in strategy or 'json_ld' in strategy or 'inline_state' in strategy
        
        print(f"✅ SUCCESS!")
        print(f"   Strategy: {strategy}")
        print(f"   Fast Path: {'🚀 YES' if fast_path else '❌ NO (fallback)'}")
        print(f"   Products: {len(products)}\n")
        
        if products:
            print(f"   Sample products:")
            for i, p in enumerate(products[:5], 1):
                print(f"   {i}. {p.get('product_name', 'N/A')}")
                print(f"      ${p.get('price', 'N/A')} {p.get('currency', '')}")
                print(f"      URL: {p.get('url', 'N/A')[:80]}")
        
        if fast_path:
            print(f"\n🎉 FAST PATH WORKING!")
        else:
            print(f"\n⚠️  Still using slow fallback...")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
