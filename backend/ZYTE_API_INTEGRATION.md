# Zyte API Integration

## Overview

Zyte API is now integrated as an alternative to the Playwright-based simple extractor. It provides:
- **Automatic bot detection bypassing** (PerimeterX, Cloudflare, etc.)
- **Smart proxy rotation** with residential proxies
- **JavaScript rendering** for SPAs
- **CAPTCHA solving**
- **Better reliability at scale**

## Test Results

### ✅ Hello Molly (Bot Protection Site)
```
URL: https://www.hellomolly.com/collections/dresses
Result: SUCCESS ✅
- Found 23 product links
- Extracted 3/3 products (100% success rate)
- Used Next.js data extraction strategy
- Bypassed bot detection successfully
```

**Example Product:**
```json
{
  "product_name": "Effortless Luxe Halter Satin Maxi Dress Navy",
  "price": "$129.00",
  "currency": "USD",
  "product_url": "https://www.hellomolly.com/products/...",
  "image_url": "https://cdn.shopify.com/..."
}
```

### ❌ Express.com (Complex SPA)
```
URL: https://www.express.com/womens-clothing/dresses
Result: FAILED ❌
- Products loaded entirely via JavaScript/API calls
- No product links in rendered HTML
- Both manual and automatic extraction failed
```

**Why it failed:**
Express.com uses a complex SPA architecture where:
1. The page renders an empty container
2. Products are fetched via API calls after page load
3. No `<a>` tags with product URLs exist in the HTML
4. Would require API reverse-engineering or Puppeteer interaction

## When to Use Zyte vs Simple Extractor

### Use Zyte API When:
- ✅ Site has bot detection (PerimeterX, Cloudflare, etc.)
- ✅ Need reliable extraction at scale
- ✅ Budget available (Zyte charges per request)
- ✅ Site has product links in HTML (even after JS rendering)

### Use Simple Extractor When:
- ✅ No bot detection on target site
- ✅ Development/testing phase
- ✅ Budget constraints
- ✅ Site is simple/static

### Neither Work Well For:
- ❌ Complex SPAs with pure API-based product loading (like Express.com)
- ❌ Sites requiring user interaction (clicks, scrolls to load)
- ❌ Sites with complex pagination

## Usage

### Method 1: Manual Extraction (Recommended)
Uses Zyte for HTML fetching, then applies your extraction strategies:

```python
from app.modules.extractors.zyte_extractor import extract_products_from_url_zyte

result = await extract_products_from_url_zyte(
    url="https://www.hellomolly.com/collections/dresses",
    max_products=50,
    use_automatic=False  # Use manual extraction
)

if result['success']:
    products = result['products']
    print(f"Extracted {len(products)} products")
```

### Method 2: Automatic Extraction (Faster but Less Accurate)
Uses Zyte's built-in AI to detect products:

```python
result = await extract_products_from_url_zyte(
    url="https://www.hellomolly.com/collections/dresses",
    max_products=50,
    use_automatic=True  # Use Zyte's AI
)
```

## Configuration

Add to your `.env` file:
```bash
ZYTE_API_KEY=your_zyte_api_key_here
```

## Cost Considerations

Zyte API pricing (approximate):
- **browserHtml** (JS rendering): ~$2-5 per 1000 requests
- **httpResponseBody** (no JS): ~$0.50-1 per 1000 requests
- **Automatic extraction**: ~$3-6 per 1000 requests

**Example costs:**
- Extract 50 products (1 listing + 50 product pages): ~$0.10-0.25
- Extract 500 products: ~$1.00-2.50

## Testing

### Test a Single Site
```bash
cd backend
source venv/bin/activate
python test_zyte_extractor.py "https://site.com/products" 10
```

### Run Full Test Suite
```bash
python test_zyte_extractor.py
```

## Limitations

1. **No magic solution**: Zyte can't extract what isn't in the HTML
2. **Cost**: Pay per request (vs free Playwright)
3. **API-only sites**: Sites like Express.com that load products via API still fail
4. **Rate limits**: Zyte has rate limits based on your plan

## Recommendations

### For Production
1. **Try Simple Extractor first** - it's free and works for many sites
2. **Fall back to Zyte** if bot detection is encountered
3. **Monitor costs** - Zyte charges per request
4. **Cache results** - avoid re-extracting same products

### For Complex Sites (like Express.com)
You'll need to:
1. Reverse-engineer their API
2. Use Puppeteer to interact with the page (click "Load More", etc.)
3. Consider selenium with undetected-chromedriver
4. Or find their sitemap/product feed

## File Structure

```
backend/app/modules/extractors/
├── simple_extractor.py     # Playwright-based (free)
├── zyte_extractor.py        # Zyte API-based (paid)
└── __init__.py              # Exports both extractors
```

## Next Steps

To integrate Zyte into your agent:
1. ✅ Zyte extractor is already exported from `extractors` module
2. Optionally add a tool in `app/tools/definitions.py` for Zyte-specific extraction
3. Or modify existing `extract_products` tool to try Zyte on failure

## Summary

**Zyte API Integration: ✅ Working**

| Site | Simple Extractor | Zyte Extractor | Winner |
|------|-----------------|----------------|---------|
| Hello Molly | ⚠️ Bot detection | ✅ Works perfectly | Zyte |
| Shopify sites | ✅ Works | ✅ Works | Simple (free) |
| Express.com | ❌ No links | ❌ No links | Neither* |

*For Express.com and similar sites, you need API reverse-engineering or advanced browser automation.
