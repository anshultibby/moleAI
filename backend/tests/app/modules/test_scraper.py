"""
Simple test for product extraction functions
"""

import pytest
import json
import requests
import os
from datetime import datetime
from app.modules.scraper import (
    extract_product_from_shopify,
    extract_product_from_js_framework,
    extract_product_from_jsonld,
    JinaAIScraper
)


@pytest.mark.integration
def test_black_heels_extraction(api_keys):
    """Simple test of 3 extraction methods on 3 black heels URLs"""
    
    # Your 3 URLs
    urls = [
        "https://www.macys.com/shop/womens/all-womens-shoes/high-heels/Color_normal/Black?id=71123",
        "https://www.misslola.com/collections/black-heels?srsltid=AfmBOorF4bM4jkCQ3W8XBChyKcMj2crxY3Sq7MUuyUWa9pPguboJXz3_",
        "https://www.dsw.com/category/womens/shoes/heels?color=Black"
    ]
    
    results = []
    
    for url in urls:
        print(f"\n🔍 Testing: {url}")
        
        # Get HTML both ways
        direct_html = get_direct_html(url)
        jina_html = get_jina_html(url, api_keys["jina_ai"]) if api_keys["jina_ai"] else ""
        
        # Test with direct HTML
        if direct_html:
            print(f"✅ Direct HTML: {len(direct_html)} chars")
            direct_results = {
                "shopify": extract_product_from_shopify(direct_html, url),
                "js_framework": extract_product_from_js_framework(direct_html, url),
                "json_ld": extract_product_from_jsonld(direct_html, url)
            }
        else:
            print("❌ Direct HTML failed")
            direct_results = {"shopify": None, "js_framework": None, "json_ld": None}
        
        # Test with Jina HTML
        if jina_html:
            print(f"✅ Jina HTML: {len(jina_html)} chars")
            jina_results = {
                "shopify": extract_product_from_shopify(jina_html, url),
                "js_framework": extract_product_from_js_framework(jina_html, url),
                "json_ld": extract_product_from_jsonld(jina_html, url)
            }
        else:
            print("❌ Jina HTML failed")
            jina_results = {"shopify": None, "js_framework": None, "json_ld": None}
        
        # Count successes
        direct_success = sum(1 for v in direct_results.values() if v is not None)
        jina_success = sum(1 for v in jina_results.values() if v is not None)
        
        print(f"📊 Direct: {direct_success}/3 methods found products")
        print(f"📊 Jina: {jina_success}/3 methods found products")
        
        results.append({
            "url": url,
            "direct_html_length": len(direct_html) if direct_html else 0,
            "jina_html_length": len(jina_html) if jina_html else 0,
            "direct_results": direct_results,
            "jina_results": jina_results
        })
    
    # Create timestamped directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"test_scraper_results/test_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # Save results JSON
    with open(f"{results_dir}/results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Save full HTML files
    for i, result in enumerate(results):
        url_name = f"url_{i+1}"
        
        if result["direct_html_length"] > 0:
            with open(f"{results_dir}/{url_name}_direct.html", "w", encoding="utf-8") as f:
                f.write(result["direct_html"])
        
        if result["jina_html_length"] > 0:
            with open(f"{results_dir}/{url_name}_jina.html", "w", encoding="utf-8") as f:
                f.write(result["jina_html"])
    
    print(f"\n💾 All results saved to: {results_dir}/")
    print(f"   - results.json (extraction results)")
    print(f"   - url_1_direct.html, url_1_jina.html (Macy's)")
    print(f"   - url_2_direct.html, url_2_jina.html (Miss Lola)")
    print(f"   - url_3_direct.html, url_3_jina.html (DSW)")


def get_direct_html(url):
    """Get HTML directly"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except:
        return ""


def get_jina_html(url, api_key):
    """Get HTML via Jina AI"""
    try:
        if not api_key:
            return ""
        scraper = JinaAIScraper(api_key)
        resource = scraper.scrape_url(url, format="html", wait_for_js=True)
        return resource.content.get("html", "")
    except:
        return ""
