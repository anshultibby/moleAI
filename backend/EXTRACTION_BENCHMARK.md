# Extraction Strategy Benchmark Tool

## Overview

Automatically tests extraction strategies against 100+ real e-commerce URLs to identify:
- Which strategies work best
- Common failure patterns  
- Sites needing special handling
- Opportunities for optimization

## What It Does

1. **Collects URLs** from Serper using real user queries
2. **Tests 3 fast strategies** on each URL:
   - JSON-LD ItemList
   - Inline JSON State (__NEXT_DATA__, __NUXT__, etc.)
   - HTML Grid Scraping
3. **Records results**:
   - Which strategy won
   - Number of products found
   - Failure reasons for each strategy
   - Shopify detection
4. **Generates insights**:
   - Success rates per strategy
   - Common failure patterns
   - Recommendations for improvements

## Quick Test (10 URLs, ~5-10 minutes)

```bash
cd /Users/anshul/code/moleAI/backend
source venv/bin/activate
python benchmark_quick_test.py
```

## Full Benchmark (100 URLs, ~30-60 minutes)

```bash
cd /Users/anshul/code/moleAI/backend
source venv/bin/activate
python benchmark_extraction_strategies.py
```

**Note**: This will use ~100 BrightData API calls. Monitor your quota!

## Output

Creates `extraction_benchmark_YYYYMMDD_HHMMSS.json` with:

```json
{
  "timestamp": "20251007_185500",
  "summary": {
    "total_tested": 100,
    "successful": 73,
    "failed": 27,
    "success_rate": "73.0%",
    "strategy_wins": {
      "html_grid": 42,
      "inline_state": 18,
      "json_ld": 13
    },
    "shopify_stats": {
      "total": 35,
      "successful": 28
    }
  },
  "results": [
    {
      "url": "https://example.com/collections/dresses",
      "domain": "example.com",
      "winning_strategy": "html_grid",
      "products_found": 20,
      "strategies_tested": {
        "json_ld": 0,
        "inline_state": 0,
        "html_grid": 20
      },
      "failure_reasons": [
        "JSON-LD: No ItemList found",
        "Inline State: No __NEXT_DATA__/etc"
      ]
    }
  ],
  "failure_analysis": {
    "JSON-LD: No ItemList found": 45,
    "Inline State: No __NEXT_DATA__": 38,
    "HTML Grid: No product cards": 15
  }
}
```

## Sample Output

```
================================================================================
📊 BENCHMARK RESULTS ANALYSIS
================================================================================

📈 Overall Success Rate:
   Total URLs tested: 100
   Fast path worked: 73 (73.0%)
   Needs fallback: 27 (27.0%)

🏆 Strategy Performance:
   🎯 HTML Grid              42 wins (57.5%)
   ⚡ Inline JSON State      18 wins (24.7%)
   📋 JSON-LD ItemList       13 wins (17.8%)

🛍️  Shopify Sites:
   Total Shopify: 35
   Successful: 28 (80.0%)

❌ Top Failure Reasons:
   [45] JSON-LD: No ItemList found in page
   [38] Inline State: No __NEXT_DATA__/__NUXT__/etc found
   [15] HTML Grid: No product cards found with common selectors
   [12] Failed to fetch HTML (timeout or empty)

📝 Recommendations:
   💡 Many sites missing common inline state patterns
      • Add support for more frameworks (Remix, Astro, etc.)
   
   🛍️  Shopify extraction needs improvement
      • Implement /collections/handle/products.json fallback
```

## Use Cases

### 1. Before Making Changes
Run benchmark to establish baseline metrics

### 2. After Strategy Updates  
Re-run to measure improvement

### 3. Finding Edge Cases
Identify sites where all strategies fail → investigate why

### 4. Prioritizing Features
See which new strategies would help most sites

## Analyzing Results

### High HTML Grid Success = Good!
Grid scraping is fastest and most reliable

### High "No ItemList" Failures
Consider adding more JSON-LD patterns or Shopify JSON endpoints

### Many Shopify Failures
Implement `/collections/handle/products.json` fallback

### Timeouts/Empty HTML
May need to increase BrightData timeout or add retries

## Next Steps After Benchmark

1. **Review `failure_analysis`** - what are the top failure reasons?

2. **Check failed sites manually** - visit URLs in browser, inspect:
   - Are products visible?
   - What JSON blobs are in the page source?
   - Is there a public JSON API?

3. **Update strategies** based on findings:
   - Add new selectors to grid scraper
   - Support more inline state patterns
   - Add framework-specific extractors

4. **Re-run benchmark** to validate improvements

## Advanced: Custom Queries

Edit `USER_QUERIES` in `benchmark_extraction_strategies.py`:

```python
USER_QUERIES = [
    "your custom query 1",
    "your custom query 2",
    # ... more queries
]
```

## Cost Estimation

- **Quick Test (10 URLs)**: ~10 BrightData API calls (~$0.10)
- **Full Benchmark (100 URLs)**: ~100 API calls (~$1.00)

Saves intermediate results every 10 URLs in case of interruption!
