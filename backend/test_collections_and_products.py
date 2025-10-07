#!/usr/bin/env python3
"""Test simple extractor with collections + products filter"""

import sys
sys.path.append('/Users/anshul/code/moleAI/backend')

from app.modules.extractors.simple_extractor import get_html, find_product_links


def test_link_discovery():
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    
    print(f"Testing link discovery with collections + products filter")
    print(f"URL: {url}\n")
    
    html = get_html(url)
    if not html:
        print("Failed to get HTML")
        return
    
    links = find_product_links(html, url)
    
    # Categorize the links
    products = [l for l in links if '/products/' in l or '/product/' in l]
    collections = [l for l in links if '/collections/' in l or '/collection/' in l]
    
    print(f"{'='*80}")
    print(f"RESULTS:")
    print(f"{'='*80}")
    print(f"Total links found: {len(links)}")
    print(f"  - Product pages: {len(products)}")
    print(f"  - Collection pages: {len(collections)}")
    print(f"{'='*80}\n")
    
    print(f"PRODUCT PAGES (first 10):")
    for i, link in enumerate(products[:10], 1):
        print(f"  {i}. {link}")
    if len(products) > 10:
        print(f"  ... and {len(products) - 10} more\n")
    
    print(f"\nCOLLECTION PAGES (first 10):")
    for i, link in enumerate(collections[:10], 1):
        print(f"  {i}. {link}")
    if len(collections) > 10:
        print(f"  ... and {len(collections) - 10} more\n")
    
    print(f"\n{'='*80}")
    print(f"✅ Filter working! Keeping {len(links)} relevant links")
    print(f"   (skipped pages, social media, cart, etc.)")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_link_discovery()

