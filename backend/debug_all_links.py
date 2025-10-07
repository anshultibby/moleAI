#!/usr/bin/env python3
"""
Debug to see EVERY link found before filtering
"""

import sys
sys.path.append('/Users/anshul/code/moleAI/backend')

from urllib.parse import urljoin
from bs4 import BeautifulSoup
from app.modules.extractors.simple_extractor import get_html


def debug_all_links(url: str):
    """Find ALL links before any filtering"""
    
    print(f"Fetching HTML from: {url}\n")
    html = get_html(url)
    
    if not html:
        print("Failed to get HTML")
        return
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all divs that contain the word 'product' anywhere
    product_divs = []
    
    for div in soup.find_all('div'):
        div_text = div.get_text().lower()
        div_attrs = ' '.join([str(v) for v in div.attrs.values()]).lower()
        
        if 'product' in div_text or 'product' in div_attrs:
            product_divs.append(div)
    
    # Also look for other common product container elements
    for element in soup.find_all(['article', 'li', 'section']):
        element_text = element.get_text().lower()
        element_attrs = ' '.join([str(v) for v in element.attrs.values()]).lower()
        
        if 'product' in element_text or 'product' in element_attrs:
            product_divs.append(element)
    
    print(f"Found {len(product_divs)} potential product containers\n")
    
    # Extract ALL links from these containers
    all_links_raw = []
    all_links_clean = []
    
    for container in product_divs:
        for link in container.find_all('a', href=True):
            href = link['href']
            
            # Skip empty hrefs, anchors, and javascript links
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Convert to absolute URL
            full_url = urljoin(url, href)
            all_links_raw.append(full_url)
            
            # Clean URL (remove fragments and query params)
            clean_url = full_url.split('#')[0].split('?')[0]
            
            if clean_url not in all_links_clean and clean_url != url:
                all_links_clean.append(clean_url)
    
    print(f"Raw links found: {len(all_links_raw)}")
    print(f"Unique clean links: {len(all_links_clean)}\n")
    
    # Categorize the clean links
    from collections import defaultdict
    categories = defaultdict(list)
    
    for link in all_links_clean:
        if '/products/' in link or '/product/' in link:
            categories['PRODUCTS'].append(link)
        elif '/collections/' in link or '/collection/' in link:
            categories['COLLECTIONS'].append(link)
        elif '/pages/' in link:
            categories['PAGES'].append(link)
        elif '/blogs/' in link or '/blog/' in link:
            categories['BLOG'].append(link)
        else:
            categories['OTHER'].append(link)
    
    print(f"{'='*80}")
    print("LINK CATEGORIES:")
    print(f"{'='*80}\n")
    
    for category, links in sorted(categories.items()):
        print(f"\n{category}: {len(links)} links")
        for i, link in enumerate(links[:10], 1):
            print(f"  {i}. {link}")
        if len(links) > 10:
            print(f"  ... and {len(links) - 10} more")
    
    # Save all links to file
    import json
    output = {
        "url": url,
        "total_raw_links": len(all_links_raw),
        "total_unique_clean_links": len(all_links_clean),
        "categories": {cat: links for cat, links in categories.items()},
        "all_clean_links": all_links_clean
    }
    
    with open("all_links_debug.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*80}")
    print("✅ Full debug output saved to: all_links_debug.json")
    print(f"{'='*80}")


if __name__ == "__main__":
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    debug_all_links(url)

