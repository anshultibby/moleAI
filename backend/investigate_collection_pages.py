#!/usr/bin/env python3
"""
Investigate why collection pages aren't working for ABC Fashion and The Dress Warehouse
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.modules.product_extractor import ProductExtractor

async def investigate_site(url: str, site_name: str):
    """Investigate a specific site's HTML structure"""
    print(f"\n{'='*60}")
    print(f"🔍 INVESTIGATING: {site_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    extractor = ProductExtractor()
    
    try:
        # Fetch the page
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={
                "User-Agent": "ProductExtractorBot/1.0 (+mailto:test@example.com)"
            }) as response:
                html = await response.text(errors="ignore")
                
                print(f"✅ Page fetched: {len(html)} characters")
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check our current selectors
                print(f"\n🔍 TESTING CURRENT SELECTORS:")
                selectors = [
                    'a[href*="/product"]',
                    'a[href*="/p/"]', 
                    'a[href*="/item"]',
                    'a[href*="/dp/"]',
                    '.product-item a',
                    '.product-card a',
                    '.product-link',
                    '[data-product-url]',
                    'a.product',
                    '.grid-product__link',
                    '.product-tile a'
                ]
                
                total_found = 0
                for selector in selectors:
                    links = soup.select(selector)
                    if links:
                        print(f"  ✅ {selector}: {len(links)} matches")
                        total_found += len(links)
                        # Show first few matches
                        for i, link in enumerate(links[:3]):
                            href = link.get('href')
                            text = link.get_text(strip=True)[:50]
                            print(f"    - {href} ({text})")
                    else:
                        print(f"  ❌ {selector}: 0 matches")
                
                print(f"\n📊 Total links found with current selectors: {total_found}")
                
                # Look for other potential product link patterns
                print(f"\n🔍 ANALYZING ALL LINKS:")
                all_links = soup.find_all('a', href=True)
                print(f"Total links on page: {len(all_links)}")
                
                # Categorize links
                product_like = []
                other_links = []
                
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Look for product-like patterns
                    if any(pattern in href.lower() for pattern in ['/product', '/p/', '/item', '/dress', '/gown']):
                        product_like.append((href, text[:50]))
                    elif href.startswith('/') and not any(skip in href.lower() for skip in ['/page', '/collection', '/search', '/account', '/cart', '/checkout', '.css', '.js', '.jpg', '.png']):
                        other_links.append((href, text[:50]))
                
                print(f"\n📦 POTENTIAL PRODUCT LINKS ({len(product_like)}):")
                for href, text in product_like[:10]:  # Show first 10
                    full_url = urljoin(url, href)
                    print(f"  - {full_url} ({text})")
                
                print(f"\n🔗 OTHER INTERNAL LINKS ({len(other_links)}):")
                for href, text in other_links[:10]:  # Show first 10
                    full_url = urljoin(url, href)
                    print(f"  - {full_url} ({text})")
                
                # Test our product link extraction method
                print(f"\n🧪 TESTING OUR EXTRACTION METHOD:")
                extracted_links = extractor._extract_product_links_from_listing(html, url)
                print(f"Our method found: {len(extracted_links)} product links")
                for link in extracted_links[:5]:
                    print(f"  - {link}")
                
                # Look for specific site patterns
                print(f"\n🔍 SITE-SPECIFIC ANALYSIS:")
                if 'abcfashion' in url:
                    # Look for ABC Fashion specific patterns
                    abc_patterns = [
                        '.product-item',
                        '.product-card', 
                        '.grid-item',
                        '[data-product-handle]',
                        '.product-wrap'
                    ]
                    for pattern in abc_patterns:
                        elements = soup.select(pattern)
                        if elements:
                            print(f"  ✅ ABC Pattern {pattern}: {len(elements)} matches")
                            # Look for links within these elements
                            for elem in elements[:3]:
                                links = elem.find_all('a', href=True)
                                for link in links:
                                    print(f"    - {link.get('href')} ({link.get_text(strip=True)[:30]})")
                        else:
                            print(f"  ❌ ABC Pattern {pattern}: 0 matches")
                
                elif 'thedresswarehouse' in url:
                    # Look for The Dress Warehouse specific patterns
                    tdw_patterns = [
                        '.product-item',
                        '.product-card',
                        '.grid-item', 
                        '.collection-item',
                        '[data-product-id]'
                    ]
                    for pattern in tdw_patterns:
                        elements = soup.select(pattern)
                        if elements:
                            print(f"  ✅ TDW Pattern {pattern}: {len(elements)} matches")
                            for elem in elements[:3]:
                                links = elem.find_all('a', href=True)
                                for link in links:
                                    print(f"    - {link.get('href')} ({link.get_text(strip=True)[:30]})")
                        else:
                            print(f"  ❌ TDW Pattern {pattern}: 0 matches")
                
    except Exception as e:
        print(f"❌ ERROR investigating {site_name}: {e}")

async def main():
    """Main investigation function"""
    sites = [
        ("https://www.abcfashion.net/collections/long-prom-dresses-under-100/black", "ABC Fashion"),
        ("https://thedresswarehouse.com/collections/evening-dresses-under-100", "The Dress Warehouse")
    ]
    
    for url, name in sites:
        await investigate_site(url, name)
    
    print(f"\n{'='*60}")
    print("🏁 INVESTIGATION COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
