#!/usr/bin/env python3
"""
Analyze all links found on a website to see patterns
"""

import sys
sys.path.append('/Users/anshul/code/moleAI/backend')

import json
from urllib.parse import urlparse
from collections import defaultdict
from app.modules.extractors.simple_extractor import get_html, find_product_links


def analyze_links(url: str, output_file: str = "link_analysis.json"):
    """Get all links and analyze patterns"""
    
    print(f"Fetching HTML from: {url}")
    html = get_html(url)
    
    if not html:
        print("Failed to get HTML")
        return
    
    print(f"Got {len(html)} characters of HTML")
    
    # Find all product links
    links = find_product_links(html, url)
    
    print(f"\nFound {len(links)} total links")
    
    # Analyze patterns
    patterns = defaultdict(list)
    
    for link in links:
        parsed = urlparse(link)
        path = parsed.path
        
        # Categorize by path patterns
        if '/products/' in path:
            patterns['individual_products'].append(link)
        elif '/product/' in path:
            patterns['individual_products'].append(link)
        elif '/collections/' in path:
            patterns['collections'].append(link)
        elif '/collection/' in path:
            patterns['collections'].append(link)
        elif '/pages/' in path:
            patterns['pages'].append(link)
        elif '/blogs/' in path or '/blog/' in path:
            patterns['blog'].append(link)
        elif '/categories/' in path or '/category/' in path:
            patterns['categories'].append(link)
        else:
            patterns['other'].append(link)
    
    # Convert to regular dict for JSON serialization
    patterns_dict = dict(patterns)
    
    # Print summary
    print(f"\n{'='*80}")
    print("LINK PATTERNS FOUND:")
    print(f"{'='*80}")
    for pattern_type, urls in patterns_dict.items():
        print(f"\n{pattern_type.upper()}: {len(urls)} links")
        # Show first 5 examples
        for i, url in enumerate(urls[:5], 1):
            print(f"  {i}. {url}")
        if len(urls) > 5:
            print(f"  ... and {len(urls) - 5} more")
    
    # Save to JSON
    output = {
        "source_url": url,
        "total_links": len(links),
        "patterns": {
            pattern: {
                "count": len(urls),
                "examples": urls[:10],  # First 10 of each
                "all_links": urls
            }
            for pattern, urls in patterns_dict.items()
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ Full analysis saved to: {output_file}")
    print(f"{'='*80}")
    
    return output


if __name__ == "__main__":
    url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
    
    analyze_links(url, "abc_fashion_links.json")

