# Google Custom Search Engine (CSE) Setup for Shopify Store Discovery

## 🔧 Setup Instructions

### 1. Create a Google Custom Search Engine
1. Go to [Google Custom Search Engine](https://cse.google.com/cse/)
2. Click "Add" or "New search engine"
3. Fill in the basic information:
   - **Name**: "Shopify Store Discovery" (or any name you prefer)
   - **Description**: "Search engine for discovering Shopify stores"

### 2. Configure Sites to Search

#### Option A: Specific Shopify Domains (Recommended)
Add these specific patterns to your CSE:

```
*.myshopify.com
*.myshopify.com/*
myshopify.com
```

#### Option B: Include Popular Custom Shopify Domains
If you want to find stores with custom domains too, also add:

```
shopify.com
*.shopify.com
site:myshopify.com
```

### 3. Advanced Settings

#### Search Features:
- ✅ **Enable "Search the entire web"** - This allows broader discovery
- ✅ **Enable "Image search"** - Useful for product images
- ✅ **Enable "SafeSearch"** - Filters inappropriate content

#### Search Settings:
- **Language**: English (or your preferred language)
- **Country**: Your target country
- **Results per page**: 10 (maximum for API)

### 4. Get Your API Credentials

#### A. Get your Search Engine ID:
1. In your CSE control panel, click "Setup"
2. Copy the **Search engine ID** (looks like: `0123456789abcdef:example`)

#### B. Get your API Key:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the "Custom Search API"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy the API key

### 5. Add to Environment Variables

Create/update your `.env` file:

```bash
GOOGLE_CSE_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_search_engine_id_here
```

## 🧪 Test Your Setup

Run this test to verify your CSE is working:

```bash
python test_cse_setup.py
```

## 🔍 CSE Configuration Examples

### For Maximum Shopify Coverage:

**Sites to search:**
```
*.myshopify.com
*.myshopify.com/collections/*
*.myshopify.com/products/*
myshopify.com
```

**Include these patterns in "Sites to search":**
- `*.myshopify.com` - Catches all Shopify subdomains
- `*.myshopify.com/*` - Includes all pages on Shopify sites
- `site:myshopify.com` - Alternative pattern for broader search

### Advanced CSE Settings:

1. **Search the entire web**: ✅ Enabled
2. **Language**: English
3. **Country**: United States (or your target market)
4. **SafeSearch**: Moderate
5. **Image search**: ✅ Enabled
6. **Promotions**: ❌ Disabled (to avoid ads)

## 🚨 Common Issues & Solutions

### Issue: "No results found"
**Solution**: Make sure you have:
- ✅ `*.myshopify.com` in sites to search
- ✅ "Search the entire web" enabled
- ✅ Correct API key and Search Engine ID

### Issue: "API quota exceeded"
**Solution**: 
- Google CSE has 100 queries/day free limit
- Consider upgrading to paid plan for production use
- Implement caching to reduce API calls

### Issue: "Getting non-Shopify results"
**Solution**:
- Remove generic domains like `*.com`
- Focus on `*.myshopify.com` only
- Use our validation layer to filter results

## 📊 Testing Your Configuration

Use our test script to verify everything works:

```python
# Test basic CSE functionality
from app.utils.google_discovery_service import GoogleDiscoveryService

service = GoogleDiscoveryService()
domains = service.discover_shopify_stores("black leggings", max_results=5)
print(f"Found {len(domains)} domains: {domains}")
```

Expected output:
```
🔍 Running 8 Google CSE queries to find diverse stores...
📦 Discovered 15 candidate domains from Google CSE
🔍 Validating 15 discovered domains...
✅ 5 domains validated as accessible
🎯 Final result: 5 validated, accessible stores
```

## 💡 Tips for Better Results

1. **Use specific patterns**: `*.myshopify.com` vs generic `*.com`
2. **Enable "entire web"**: Finds more stores
3. **Set proper language/country**: Gets regional results
4. **Monitor quotas**: Track your API usage
5. **Cache results**: Reduce repeated API calls

## 🔄 Alternative: Manual Domain List

If CSE isn't working, you can use a curated list:

```python
# In google_discovery_service.py
FALLBACK_SHOPIFY_DOMAINS = [
    "shop.gymshark.com",
    "us.allbirds.com",
    "shop.bombas.com",
    "shop.glossier.com",
    "fenty.com",
    # Add more known working domains
]
``` 