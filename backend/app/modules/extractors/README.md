# Simple Product Extractor

A clean, simple product extraction system using a 3-step heuristic.

## The Approach

**Simple 3-step heuristic:**

1. **Get HTML** from the listing page URL
2. **Find product links** - all href links in divs/containers containing the word 'product'
3. **Extract JSON-LD** structured data from each product page

That's it. Clean, simple, effective.

## Usage

```python
from app.modules.extractors import extract_products_simple

# Extract products from any listing page
result = await extract_products_simple("https://shop.mango.com/us/women/dresses")

if result['success']:
    products = result['products']
    print(f"Found {len(products)} products")
    
    for product in products:
        print(f"- {product['title']}: ${product.get('price', 'N/A')}")
```

## What You Get

```json
{
  "success": true,
  "products": [
    {
      "title": "Floral Midi Dress",
      "price": 89.99,
      "currency": "USD",
      "brand": "Mango",
      "product_url": "https://shop.mango.com/us/product/123",
      "image_url": "https://shop.mango.com/images/dress.jpg",
      "sku": "67040504",
      "description": "Midi dress with floral print..."
    }
  ],
  "meta": {
    "strategy": "simple_json_ld",
    "total_links_found": 24,
    "products_extracted": 18,
    "success_rate": 0.75
  }
}
```

## Why This Works

- **Most e-commerce sites** have divs with 'product' in class names or text
- **JSON-LD is standard** for structured data (Google requires it)
- **Simple = reliable** - fewer things to break
- **Fast** - direct extraction from structured data

## Test It

```bash
cd backend
python test_simple_extractor.py
```

## Configuration

```python
# Limit number of products
result = await extract_products_simple(url, max_products=20)
```

## Requirements

- `requests` - for HTTP requests
- `beautifulsoup4` - for HTML parsing  
- `aiohttp` - for concurrent requests

## When It Works Best

✅ **Sites with proper JSON-LD markup** (most modern e-commerce)  
✅ **Product containers with 'product' in class/text** (very common pattern)  
✅ **Static or server-rendered pages** (no JS required)

## When It Doesn't Work

❌ **Sites without JSON-LD** (rare for modern e-commerce)  
❌ **No 'product' in container elements** (uncommon but possible)  
❌ **Heavy JavaScript sites** with no server-side rendering

## Files

- `simple_extractor.py` - Main extraction logic (200 lines)
- `test_simple_extractor.py` - Test script
- `README.md` - This documentation

## The Beauty of Simple

Instead of complex browser automation, LLM orchestration, or site-specific scrapers, this approach leverages two facts:

1. **E-commerce sites want to be found** → they use standard JSON-LD
2. **Product URLs are predictable** → they contain 'product'

Simple, reliable, and works across most sites.
