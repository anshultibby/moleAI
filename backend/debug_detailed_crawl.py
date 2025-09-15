#!/usr/bin/env python3
"""
Debug detailed crawl with custom logging
"""

import asyncio
import aiohttp
from collections import deque
from app.modules.product_extractor import ProductExtractor

async def debug_detailed_crawl():
    """Debug with detailed logging of what happens to each URL"""
    
    extractor = ProductExtractor()
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    
    print(f"🔍 DETAILED CRAWL DEBUG")
    print(f"URL: {url}")
    print(f"={'='*80}")
    
    # Manually implement a simplified version of the crawl with detailed logging
    start_url = extractor._canonicalize(url)
    seen = set([start_url])
    queue = deque([(start_url, 0)])
    results = []
    
    conn = aiohttp.TCPConnector(limit=extractor.CONCURRENCY)
    async with aiohttp.ClientSession(
        headers={"User-Agent": extractor.USER_AGENT}, 
        connector=conn
    ) as session:
        
        step = 0
        while queue and step < 10:  # Limit steps for debugging
            step += 1
            print(f"\n--- STEP {step} ---")
            print(f"Queue size: {len(queue)}")
            print(f"Seen URLs: {len(seen)}")
            
            # Process one URL at a time for detailed logging
            if queue:
                current_url, depth = queue.popleft()
                print(f"Processing: {current_url} (depth {depth})")
                
                # Fetch page
                try:
                    async with session.get(current_url, timeout=extractor.TIMEOUT) as resp:
                        if resp.status != 200:
                            print(f"  ❌ Bad status: {resp.status}")
                            continue
                        html = await resp.text(errors="ignore")
                        final_url = str(resp.url)
                        print(f"  ✅ Fetched: {len(html)} chars")
                        
                        # Extract products
                        products = extractor._extract_products_from_html(html, final_url)
                        print(f"  📦 Products found: {len(products)}")
                        
                        if products:
                            for i, product in enumerate(products, 1):
                                print(f"    Product {i}: {product.get('name', 'N/A')}")
                                print(f"      Price: {product.get('price', 'N/A')}")
                                print(f"      Brand: {product.get('brand', 'N/A')}")
                            results.extend(products)
                        
                        # Check page type and extract links
                        page_type = extractor._classify_url(final_url)
                        print(f"  🏷️ Page type: {page_type}")
                        
                        if page_type == "listing":
                            product_links = extractor._extract_product_links_from_listing(html, final_url)
                            print(f"  🔗 Product links found: {len(product_links)}")
                            
                            # Add first few product links to queue
                            for product_url in product_links[:5]:  # Just first 5 for debugging
                                if product_url not in seen:
                                    seen.add(product_url)
                                    queue.appendleft((product_url, depth + 1))
                                    print(f"    Added to queue: {product_url} (depth {depth + 1})")
                        
                        # Check depth limit
                        if depth >= extractor.MAX_DEPTH:
                            print(f"  ⚠️ Max depth reached ({depth} >= {extractor.MAX_DEPTH})")
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Total products found: {len(results)}")
    print(f"Total URLs seen: {len(seen)}")

if __name__ == "__main__":
    asyncio.run(debug_detailed_crawl())
