"""
Comprehensive Extraction Strategy Benchmark

1. Use Serper to find 100+ e-commerce URLs from real user queries
2. Test all fast extraction strategies on each URL
3. Record which strategies work and why others fail
4. Generate insights for strategy improvements
"""
import asyncio
import json
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Any
from collections import Counter

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.modules.serp import search_web
from app.modules.extractors.brightdata_api_extractor import get_html_with_brightdata_api
from app.modules.extractors.simple_extractor import (
    extract_products_from_listing_json_ld,
    extract_products_from_inline_state,
    extract_products_from_html_grid,
    is_shopify
)


# Real user queries from frontend
USER_QUERIES = [
    "black dresses under $100",
    "elegant evening gowns",
    "summer maxi dresses",
    "cocktail dresses for wedding",
    "casual midi dresses",
    "formal prom dresses",
    "boho style dresses",
    "little black dress",
    "floral print dresses",
    "long sleeve dresses",
    "party dresses under $50",
    "vintage style dresses",
    "wrap dresses",
    "off shoulder dresses",
    "sequin party dresses",
]


async def collect_urls_from_serper(queries: List[str], urls_per_query: int = 10) -> List[Dict[str, str]]:
    """Collect e-commerce URLs from Serper search results"""
    
    all_urls = []
    seen_domains = set()
    
    print(f"\n{'='*80}")
    print(f"📡 COLLECTING URLs FROM SERPER")
    print(f"{'='*80}\n")
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Searching: {query}")
        
        try:
            # search_web is sync, so run in executor
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: search_web(query, num_results=urls_per_query))
            
            if results and results.get('results'):
                for result in results['results']:
                    url = result.get('url', '')
                    title = result.get('title', '')
                    domain = url.split('/')[2] if '/' in url else ''
                    
                    # Skip duplicates from same domain
                    if domain in seen_domains:
                        continue
                    
                    # Only keep e-commerce URLs (collection/category/listing pages)
                    if any(pattern in url.lower() for pattern in [
                        '/collections/', '/collection/', '/category/', '/categories/',
                        '/products/', '/shop/', '/dresses/', '/clothing/',
                        '/browse/', '/search?', '/s/'
                    ]):
                        all_urls.append({
                            'url': url,
                            'title': title,
                            'query': query,
                            'domain': domain
                        })
                        seen_domains.add(domain)
                        print(f"   ✓ Added: {domain}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    print(f"\n📊 Collected {len(all_urls)} unique URLs from {len(seen_domains)} domains")
    return all_urls


async def test_extraction_strategies(url: str, domain: str) -> Dict[str, Any]:
    """Test all fast extraction strategies on a URL and record results"""
    
    result = {
        'url': url,
        'domain': domain,
        'html_fetched': False,
        'html_size': 0,
        'is_shopify': False,
        'strategies_tested': {},
        'products_found': 0,
        'winning_strategy': None,
        'failure_reasons': []
    }
    
    # Fetch HTML
    print(f"\n{'─'*80}")
    print(f"🧪 Testing: {domain}")
    print(f"{'─'*80}")
    
    try:
        html = await get_html_with_brightdata_api(url, render_js=True, timeout=45)
        
        if not html:
            result['failure_reasons'].append('Failed to fetch HTML (timeout or empty)')
            print("❌ Failed to fetch HTML")
            return result
        
        result['html_fetched'] = True
        result['html_size'] = len(html)
        result['is_shopify'] = is_shopify(html)
        
        print(f"✓ Fetched {len(html):,} bytes")
        if result['is_shopify']:
            print("🛍️  Detected: Shopify site")
        
    except Exception as e:
        result['failure_reasons'].append(f'Fetch error: {str(e)}')
        print(f"❌ Fetch error: {e}")
        return result
    
    # Strategy 1: JSON-LD ItemList
    print("\n📋 Testing: JSON-LD ItemList")
    try:
        products_jsonld = extract_products_from_listing_json_ld(html, url)
        result['strategies_tested']['json_ld'] = len(products_jsonld)
        
        if products_jsonld:
            print(f"   ✅ SUCCESS: {len(products_jsonld)} products")
            if not result['winning_strategy']:
                result['winning_strategy'] = 'json_ld'
                result['products_found'] = len(products_jsonld)
        else:
            print(f"   ❌ No products found")
            result['failure_reasons'].append('JSON-LD: No ItemList found in page')
    except Exception as e:
        result['strategies_tested']['json_ld'] = 0
        result['failure_reasons'].append(f'JSON-LD error: {str(e)}')
        print(f"   ❌ Error: {e}")
    
    # Strategy 2: Inline JSON State
    print("\n⚡ Testing: Inline JSON State")
    try:
        products_state = extract_products_from_inline_state(html, url, max_products=20)
        result['strategies_tested']['inline_state'] = len(products_state)
        
        if products_state:
            print(f"   ✅ SUCCESS: {len(products_state)} products")
            if not result['winning_strategy']:
                result['winning_strategy'] = 'inline_state'
                result['products_found'] = len(products_state)
        else:
            print(f"   ❌ No products found")
            result['failure_reasons'].append('Inline State: No __NEXT_DATA__/__NUXT__/etc found')
    except Exception as e:
        result['strategies_tested']['inline_state'] = 0
        result['failure_reasons'].append(f'Inline State error: {str(e)}')
        print(f"   ❌ Error: {e}")
    
    # Strategy 3: HTML Grid
    print("\n🎯 Testing: HTML Grid Scraping")
    try:
        products_grid = extract_products_from_html_grid(html, url, max_products=20)
        result['strategies_tested']['html_grid'] = len(products_grid)
        
        if products_grid:
            print(f"   ✅ SUCCESS: {len(products_grid)} products")
            if not result['winning_strategy']:
                result['winning_strategy'] = 'html_grid'
                result['products_found'] = len(products_grid)
        else:
            print(f"   ❌ No products found")
            result['failure_reasons'].append('HTML Grid: No product cards found with common selectors')
    except Exception as e:
        result['strategies_tested']['html_grid'] = 0
        result['failure_reasons'].append(f'HTML Grid error: {str(e)}')
        print(f"   ❌ Error: {e}")
    
    # Summary
    if result['winning_strategy']:
        strategy_names = {
            'json_ld': '📋 JSON-LD ItemList',
            'inline_state': '⚡ Inline JSON State',
            'html_grid': '🎯 HTML Grid'
        }
        print(f"\n✅ WINNER: {strategy_names[result['winning_strategy']]} ({result['products_found']} products)")
    else:
        print(f"\n❌ ALL STRATEGIES FAILED - needs fallback to individual product fetching")
        result['failure_reasons'].append('All fast paths failed - requires individual product page fetching')
    
    return result


async def main():
    """Run comprehensive benchmark"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'extraction_benchmark_{timestamp}.json'
    
    print(f"\n{'='*80}")
    print(f"🚀 EXTRACTION STRATEGY BENCHMARK")
    print(f"{'='*80}")
    print(f"Target: 100+ e-commerce URLs")
    print(f"Strategies: JSON-LD ItemList, Inline State, HTML Grid")
    print(f"Output: {output_file}")
    print(f"{'='*80}\n")
    
    # Step 1: Collect URLs
    urls_data = await collect_urls_from_serper(USER_QUERIES, urls_per_query=10)
    
    if not urls_data:
        print("\n❌ No URLs collected. Check Serper API key.")
        return
    
    # Limit to 100 for reasonable runtime
    urls_data = urls_data[:100]
    
    # Step 2: Test each URL
    print(f"\n{'='*80}")
    print(f"🧪 TESTING EXTRACTION STRATEGIES")
    print(f"{'='*80}")
    
    results = []
    
    for i, url_info in enumerate(urls_data, 1):
        print(f"\n[{i}/{len(urls_data)}] Testing: {url_info['domain']}")
        
        result = await test_extraction_strategies(url_info['url'], url_info['domain'])
        result['query'] = url_info['query']
        result['title'] = url_info['title']
        results.append(result)
        
        # Save intermediate results every 10 URLs
        if i % 10 == 0:
            with open(output_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'total_urls': len(urls_data),
                    'tested': i,
                    'results': results
                }, f, indent=2)
            print(f"\n💾 Saved intermediate results ({i}/{len(urls_data)})")
    
    # Step 3: Analyze results
    print(f"\n{'='*80}")
    print(f"📊 BENCHMARK RESULTS ANALYSIS")
    print(f"{'='*80}\n")
    
    total_tested = len(results)
    successful = len([r for r in results if r['winning_strategy']])
    failed = total_tested - successful
    
    # Strategy success rates
    strategy_wins = Counter([r['winning_strategy'] for r in results if r['winning_strategy']])
    
    print(f"📈 Overall Success Rate:")
    print(f"   Total URLs tested: {total_tested}")
    print(f"   Fast path worked: {successful} ({successful/total_tested*100:.1f}%)")
    print(f"   Needs fallback: {failed} ({failed/total_tested*100:.1f}%)")
    
    print(f"\n🏆 Strategy Performance:")
    strategy_names = {
        'json_ld': '📋 JSON-LD ItemList',
        'inline_state': '⚡ Inline JSON State',
        'html_grid': '🎯 HTML Grid'
    }
    for strategy, count in strategy_wins.most_common():
        print(f"   {strategy_names.get(strategy, strategy):25} {count:3} wins ({count/successful*100:.1f}%)")
    
    # Shopify analysis
    shopify_sites = [r for r in results if r['is_shopify']]
    shopify_successful = [r for r in shopify_sites if r['winning_strategy']]
    
    print(f"\n🛍️  Shopify Sites:")
    print(f"   Total Shopify: {len(shopify_sites)}")
    print(f"   Successful: {len(shopify_successful)} ({len(shopify_successful)/len(shopify_sites)*100:.1f}%)")
    
    # Common failure reasons
    print(f"\n❌ Top Failure Reasons:")
    all_reasons = []
    for r in results:
        if not r['winning_strategy']:
            all_reasons.extend(r['failure_reasons'])
    
    reason_counts = Counter(all_reasons)
    for reason, count in reason_counts.most_common(10):
        print(f"   [{count:2}] {reason}")
    
    # Sites needing attention
    print(f"\n🔧 Sites Needing Improvement (all strategies failed):")
    failed_sites = [r for r in results if not r['winning_strategy']]
    for r in failed_sites[:10]:
        print(f"   - {r['domain']}")
        print(f"     Reasons: {', '.join(r['failure_reasons'][:2])}")
    
    # Save final results
    final_output = {
        'timestamp': timestamp,
        'summary': {
            'total_tested': total_tested,
            'successful': successful,
            'failed': failed,
            'success_rate': f"{successful/total_tested*100:.1f}%",
            'strategy_wins': dict(strategy_wins),
            'shopify_stats': {
                'total': len(shopify_sites),
                'successful': len(shopify_successful)
            }
        },
        'queries_used': USER_QUERIES,
        'results': results,
        'failure_analysis': dict(reason_counts.most_common(20))
    }
    
    with open(output_file, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ BENCHMARK COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"\n📝 Recommendations:")
    
    # Generate recommendations
    if failed / total_tested > 0.3:
        print(f"   ⚠️  High failure rate ({failed/total_tested*100:.1f}%) - consider:")
        print(f"      • Adding Shopify JSON endpoint fallback")
        print(f"      • More inline state patterns (__STOREFRONT_DATA__, etc.)")
        print(f"      • Lower HTML grid threshold (accept 1+ cards instead of 3+)")
    
    if 'Inline State: No __NEXT_DATA__' in [r for reasons in all_reasons for r in [reasons]]:
        print(f"   💡 Many sites missing common inline state patterns")
        print(f"      • Add support for more frameworks (Remix, Astro, etc.)")
    
    if len(shopify_sites) > 10 and len(shopify_successful) / len(shopify_sites) < 0.8:
        print(f"   🛍️  Shopify extraction needs improvement")
        print(f"      • Implement /collections/handle/products.json fallback")
    
    print(f"\n")


if __name__ == "__main__":
    asyncio.run(main())
