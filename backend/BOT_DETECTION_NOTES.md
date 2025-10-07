# Bot Detection & Evasion

## Issues Encountered

### Sites with Strong Bot Detection:
- **Lulus** - 403 Forbidden, blocks both headless and simple requests
- **Express** - 403 Forbidden, timeout on JS rendering
- **Other major retailers** - Use sophisticated bot detection (Cloudflare, DataDome, etc.)

### Symptoms:
- 403 HTTP errors
- Very small HTML responses (< 10KB when should be > 100KB)
- Timeout on network idle (heavy anti-bot JS)
- Empty product listings even after JS renders

## Solutions Implemented

### 1. Enhanced Playwright Bot Evasion
```python
# Browser launch args
--disable-blink-features=AutomationControlled  # Hide automation flag
--disable-dev-shm-usage                        # Stability
--no-sandbox                                    # Compatibility

# Browser context
- Realistic viewport (1920x1080)
- Proper user agent
- Locale and timezone settings

# JavaScript injection
- Remove navigator.webdriver flag
- Makes browser appear non-automated
```

### 2. Realistic HTTP Headers
Both Playwright and requests now use full header sets:
- Accept headers (HTML, images, etc.)
- Accept-Language, Accept-Encoding
- Sec-Fetch-* headers (Chrome-specific)
- Referer from Google
- DNT (Do Not Track)
- Connection keep-alive

### 3. Smarter Timeouts
- Increased default timeout to 30s
- Use `domcontentloaded` instead of `networkidle` first
- Continue even if networkidle times out
- Wait 3s for dynamic content

### 4. Detection Warnings
- Logs warning if response < 15KB (likely blocked)
- Helps identify which sites need special handling

## Remaining Challenges

### Sites That Still Block:
1. **Major retailers with enterprise bot detection**
   - Lulus, Express, Nordstrom, etc.
   - Use DataDome, PerimeterX, Cloudflare Bot Management
   
2. **What they detect:**
   - Headless browser indicators
   - Missing browser APIs (canvas, WebGL fingerprints)
   - Mouse/scroll patterns (or lack thereof)
   - IP reputation
   - TLS fingerprints

### Solutions for Difficult Sites:

#### Option 1: Playwright Stealth Plugin
```python
# Requires: playwright-stealth
from playwright_stealth import stealth_async

page = await context.new_page()
await stealth_async(page)
```

#### Option 2: Undetected ChromeDriver
```python
# For Python: undetected-chromedriver
import undetected_chromedriver as uc
```

#### Option 3: Residential Proxies
- Rotate IP addresses
- Use residential/mobile IPs
- Services: Bright Data, Oxylabs, etc.

#### Option 4: CAPTCHA Solving
- Services: 2Captcha, Anti-Captcha
- Automatic CAPTCHA solving

#### Option 5: Site-Specific Strategies
Some sites have API endpoints or JSON data:
```
# Example: Shopify sites
https://site.com/products.json
https://site.com/collections/xyz/products.json

# Example: WooCommerce
REST API endpoints if available
```

## Best Practices

### For General Sites (Working Well):
✅ Hello Molly - Next.js data works perfectly
✅ Shopify stores - JSON-LD or Next.js data
✅ Small/medium e-commerce - Current setup sufficient

### For Protected Sites (Needs Extra Work):
- May need residential proxies
- Consider official APIs if available
- Rate limiting (respect robots.txt)
- Session management (cookies)

## Current Status

### What Works:
- ✅ JavaScript-rendered SPAs (Hello Molly, etc.)
- ✅ Standard e-commerce with JSON-LD
- ✅ Shopify stores using Next.js
- ✅ Sites with moderate bot protection

### What Needs Enhancement:
- ❌ Enterprise bot detection (DataDome, PerimeterX)
- ❌ Sites requiring CAPTCHA solving
- ❌ Sites with aggressive rate limiting

## Recommendations

1. **For immediate use:**
   - Use current extractor for Shopify/standard sites
   - Works well for 70-80% of e-commerce sites
   
2. **For protected sites:**
   - Consider official APIs first
   - Use specialized scraping services
   - Or implement advanced evasion (stealth, proxies)

3. **Rate limiting:**
   - Add delays between requests (already has 3s)
   - Implement request queue system
   - Respect robots.txt

4. **Monitoring:**
   - Log HTML response sizes
   - Track success rates per domain
   - Adjust strategy per site

