#!/usr/bin/env python3
"""
Targeted test to find the exact crawler bug
"""

import asyncio
import aiohttp
from collections import deque
from app.modules.product_extractor import ProductExtractor

async def test_crawler_bug():
    """Test the exact crawler logic to find the bug"""
    
    extractor = ProductExtractor()
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    
    print(f"🔍 TESTING CRAWLER BUG")
    print(f"URL: {url}")
    print(f"={'='*60}")
    
    # Step 1: Test product link extraction
    print(f"\n1️⃣ TESTING PRODUCT LINK EXTRACTION")
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers={"User-Agent": extractor.USER_AGENT}) as response:
            html = await response.text(errors="ignore")
            
            product_links = extractor._extract_product_links_from_listing(html, url)
            print(f"✅ Found {len(product_links)} product links")
            
            # Test first 3 product links directly
            print(f"\n2️⃣ TESTING INDIVIDUAL PRODUCT EXTRACTION")
            for i, product_url in enumerate(product_links[:3], 1):
                print(f"\nTesting product {i}: {product_url}")
                
                try:
                    async with session.get(product_url, headers={"User-Agent": extractor.USER_AGENT}) as resp:
                        if resp.status != 200:
                            print(f"  ❌ Status {resp.status}")
                            continue
                        
                        product_html = await resp.text(errors="ignore")
                        products = extractor._extract_products_from_html(product_html, str(resp.url))
                        
                        print(f"  ✅ Status {resp.status}, Products: {len(products)}")
                        if products:
                            product = products[0]
                            print(f"    Name: {product.get('name', 'N/A')}")
                            print(f"    Price: {product.get('price', 'N/A')}")
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
    
    # Step 3: Test the actual crawler with minimal setup
    print(f"\n3️⃣ TESTING MINIMAL CRAWLER LOGIC")
    
    start_url = extractor._canonicalize(url)
    seen = set([start_url])
    queue = deque([(start_url, 0)])
    results = []
    max_pages = 10  # Very limited for testing
    
    conn = aiohttp.TCPConnector(limit=extractor.CONCURRENCY)
    async with aiohttp.ClientSession(
        headers={"User-Agent": extractor.USER_AGENT}, 
        connector=conn
    ) as session:
        
        iteration = 0
        while queue and len(seen) < max_pages and iteration < 5:  # Limit iterations
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            print(f"Queue size: {len(queue)}")
            print(f"Next URLs in queue:")
            for i, (u, d) in enumerate(list(queue)[:5]):
                print(f"  {i+1}. {u} (depth {d})")
            
            # Process one batch
            batch = []
            while queue and len(batch) < extractor.CONCURRENCY:
                batch.append(queue.popleft())
            
            print(f"Processing batch of {len(batch)} URLs")
            
            tasks = [extractor._fetch_page(session, u) for (u, _) in batch]
            pages = await asyncio.gather(*tasks)
            
            for (html, final_url), (u, d) in zip(pages, batch):
                if not html:
                    print(f"  ❌ No HTML for {u}")
                    continue
                
                print(f"  ✅ Processing {final_url} (depth {d})")
                
                # Extract products
                products = extractor._extract_products_from_html(html, final_url)
                print(f"    Products found: {len(products)}")
                
                if products:
                    results.extend(products)
                    for product in products:
                        print(f"      - {product.get('name', 'N/A')} (${product.get('price', 'N/A')})")
                
                # Extract product links if listing page
                page_type = extractor._classify_url(final_url)
                print(f"    Page type: {page_type}")
                
                if page_type == "listing":
                    product_links = extractor._extract_product_links_from_listing(html, final_url)
                    print(f"    Product links found: {len(product_links)}")
                    
                    # Add first few to queue
                    added_count = 0
                    for product_url in product_links[:5]:  # Limit for testing
                        if product_url not in seen:
                            seen.add(product_url)
                            queue.appendleft((product_url, d + 1))
                            added_count += 1
                    print(f"    Added {added_count} new URLs to queue")
                
                # Check depth limit
                if d >= extractor.MAX_DEPTH:
                    print(f"    ⚠️ Max depth reached ({d} >= {extractor.MAX_DEPTH})")
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Total products found: {len(results)}")
    print(f"Total URLs seen: {len(seen)}")
    
    if results:
        print(f"\nProducts:")
        for i, product in enumerate(results, 1):
            print(f"  {i}. {product.get('name', 'N/A')} - ${product.get('price', 'N/A')}")
    else:
        print(f"❌ BUG CONFIRMED: No products found despite working individual extraction")

if __name__ == "__main__":
    asyncio.run(test_crawler_bug())
