# Troubleshooting Product Extraction

## Common Issues

### Timeout Errors

**Error:** `BrightData API timeout for [URL]`

**Causes:**
- Site has very heavy JavaScript (like Nordstrom)
- Complex rendering taking longer than timeout
- BrightData temporarily slow

**Solutions:**

1. **Increase timeout** (already set to 120 seconds by default)
2. **Try a more specific URL**:
   - ❌ Generic: `https://www.nordstrom.com/browse/women/clothing/dresses`
   - ✅ Category: `https://www.nordstrom.com/browse/women/clothing/dresses/casual`
   - ✅ Direct product: `https://www.nordstrom.com/s/dress-name/12345`

3. **Use filters in URL**:
   ```
   # Instead of browsing all dresses
   /browse/women/clothing/dresses
   
   # Filter by category/price
   /browse/women/clothing/dresses/under-100?filterByColor=black
   ```

4. **Check BrightData status**: https://brightdata.com/cp/zones
   - Check if your zone is active
   - Verify account balance
   - Review request logs

---

### No Product Links Found

**Error:** `No product links found`

**Causes:**
- URL pattern not matching (site uses unusual URL structure)
- Products loaded via infinite scroll/lazy loading
- Wrong page type (category vs product listing)

**Solutions:**

1. **Check URL patterns supported**:
   ```python
   # Currently supported patterns:
   '/products/', '/product/', '/p/', '/pro/', '/pd/', '/dp/', '/item/'
   ```

2. **Try different page types**:
   - Category pages (usually better)
   - Collection pages
   - Search results pages

3. **Look for direct product links**:
   ```bash
   # Example: Get specific dresses
   /collections/dresses          # Good
   /collections/new-arrivals     # May have mixed products
   /search?q=dresses            # May work
   ```

---

### Low Success Rate

**Issue:** Some products extracted but not all (e.g., 1/3 success)

**Causes:**
- Some product URLs have special characters
- Duplicate URLs with different parameters
- Some products don't have structured data

**Solutions:**

1. **URL encoding** (already implemented)
2. **Check product URLs** in logs
3. **Try different extraction strategies**

---

### High Costs

**Issue:** Using too many requests

**Solutions:**

1. **Reduce max_products**:
   ```python
   result = await extract_products_from_url_brightdata_api(
       url,
       max_products=10  # Instead of 50
   )
   ```

2. **Cache results**:
   ```python
   # Store extracted products in database
   # Don't re-extract same URLs
   ```

3. **Use more specific URLs**:
   - Instead of extracting 100 products from main page
   - Extract 10 products from 10 category pages

4. **Monitor usage**: https://brightdata.com/cp/zones

---

## Site-Specific Issues

### Nordstrom

**Issue:** Timeouts common, heavy JavaScript

**Solution:**
- Use category-specific URLs
- Add filters to URL (`?filterByColor=black`)
- Reduce max_products to 5-10
- May need 180+ second timeout for some pages

Example:
```python
# Instead of
url = "https://www.nordstrom.com/browse/women/clothing/dresses/under-100?filterByColor=black"

# Try
url = "https://www.nordstrom.com/browse/women/clothing/dresses/casual"
# Or specific product
url = "https://www.nordstrom.com/s/product-name/12345"
```

### Express.com

**Issue:** Some URLs with spaces fail

**Solution:** Already handled - URLs are auto-encoded

### Complex SPAs (React/Vue/Next.js)

**Issue:** Products not in initial HTML

**Solution:** BrightData renders JavaScript - should work. If not:
1. Try category pages instead of search
2. Look for sitemap or product feeds
3. Check if site has an API

---

## Debug Tips

### 1. Test with Simple URL First

```bash
# Test with known-good site
python test_brightdata_api.py "https://www.hellomolly.com/collections/dresses" 2
```

### 2. Check Logs

Look for:
- `✓ BrightData API fetched X chars` - HTML received
- `Found X unique product links` - Links discovered
- `✓ JSON-LD extracted` - Successful extraction

### 3. Check BrightData Dashboard

Visit: https://brightdata.com/cp/zones
- View request logs
- Check success/failure rates
- See exact errors from BrightData

### 4. Verify Credentials

```bash
# Check .env file
cat backend/.env | grep BRIGHTDATA

# Should see:
# BRIGHTDATA_API_KEY=your_key
# BRIGHTDATA_ZONE=web_unlocker1
```

---

## Performance Optimization

### Reduce Timeout for Fast Sites

```python
result = await extract_products_brightdata_api(
    url,
    max_products=10,
    timeout=60  # Instead of 120
)
```

### Increase Concurrency

```python
# In brightdata_api_extractor.py
await extract_products_via_brightdata_api(
    product_links,
    max_concurrent=10,  # Instead of 5
    timeout=120
)
```

### Site-Specific Settings

```python
# Fast sites
FAST_SITES = ['hellomolly.com', 'fashionnova.com']
timeout = 60 if any(site in url for site in FAST_SITES) else 120

# Slow sites
SLOW_SITES = ['nordstrom.com', 'macys.com']
timeout = 180 if any(site in url for site in SLOW_SITES) else 120
```

---

## When BrightData Won't Work

Some sites are too complex even for BrightData:

1. **Infinite scroll without links** - No product URLs in HTML
2. **Pure API-based** - Products loaded entirely via JavaScript fetch
3. **Login required** - BrightData can't authenticate
4. **Aggressive rate limiting** - Application-level blocks

**Alternatives:**
- Find sitemap.xml or product feeds
- Reverse-engineer the site's API
- Use official APIs if available
- Contact site for data partnership

---

## Getting Help

1. **BrightData Support**:
   - Email: support@brightdata.com
   - Live chat in dashboard
   - Response time: Usually 1-2 hours

2. **Check Documentation**:
   - BrightData: https://docs.brightdata.com
   - Our docs: `/backend/PRODUCT_EXTRACTION.md`

3. **Common Error Codes**:
   - **400**: Invalid URL or parameters
   - **401**: Invalid API key
   - **403**: Insufficient credits
   - **429**: Rate limit exceeded
   - **500**: BrightData internal error
   - **Timeout**: Site too slow or complex

---

## Quick Fixes

```python
# Timeout? Increase it
timeout=180

# No links? Try different URL
url = url + "/collections/dresses"  # Add specific collection

# High cost? Reduce products
max_products=5

# Low success? Check logs
logger.setLevel("DEBUG")
```
