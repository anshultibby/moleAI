# Debug Tracking System

The debug tracking system creates comprehensive artifacts for every search query, allowing you to review all decisions made during the shopping pipeline.

## Overview

Each query gets its own folder with timestamped artifacts that capture:

- **Shopify JSON data** at each filtering stage
- **Prefiltering decisions** (what was kept/removed and why)
- **LLM selection decisions** (which products were chosen and criteria used)
- **URL validation results** (invalid links/domains with reasons)
- **Detailed timing metrics** for each phase
- **Error tracking** with context

## Folder Structure

Each debug session creates a folder: `debug/{YYYYMMDD_HHMMSS}_{query_hash}/`

### Files Created

- **`session_data.json`** - Complete session data in structured format
- **`shopify_raw_sample.json`** - Sample of raw Shopify JSON (first 10 items)
- **`shopify_prefiltered.json`** - Products after prefiltering
- **`shopify_filtered.json`** - Final filtered products
- **`llm_selections.json`** - Detailed LLM selection decisions
- **`SUMMARY.txt`** - Human-readable summary report

## Key Tracking Features

### 1. Shopify Data Pipeline
```python
# Tracks data at each stage
debug_tracker.track_shopify_json(raw_data, prefiltered, filtered)

# Individual filtering decisions
debug_tracker.track_prefilter_decision(product, "Wrong category", "removed")
debug_tracker.track_filter_decision(product, "Passed all criteria", "kept")
```

### 2. LLM Decision Tracking
```python
# Track what LLM selected and why
debug_tracker.track_llm_selection(
    selected_products=final_products,
    criteria=["Quality", "Price", "Relevance"],
    rejected=rejected_products
)
```

### 3. URL Validation Tracking
```python
# Track invalid URLs with specific reasons
debug_tracker.track_invalid_url("http://bad-url.com", "HTTP 404", "domain")
debug_tracker.track_validation_error("https://broken.com", "Connection timeout")
```

### 4. Performance Timing
```python
# Time specific phases
debug_tracker.start_timing_phase("shopify_search")
# ... do work ...
debug_tracker.end_timing_phase("shopify_search")
```

## Sample Summary Report

```
DEBUG SUMMARY REPORT
===================

Query: black leather jacket women
Session ID: 20241201_143022_a8b3c7d1
Total Duration: 4.532 seconds

SHOPIFY DATA PROCESSING:
- Raw JSON items: 1,247
- After prefiltering: 89
- After main filtering: 12
- Prefilter decisions: 1,158
- Filter decisions: 77

LLM DECISIONS:
- Products selected: 5
- Products rejected: 7
- Selection criteria: 4

URL VALIDATION:
- Invalid links: 3
- Invalid domains: 8
- Validation errors: 2

TIMING BREAKDOWN:
- shopify_search: 2.341s
- llm_filter: 1.203s
- url_validation: 0.789s
- store_discovery: 0.199s

FINAL RESULTS:
- Products shown to user: 5
- Links shown to user: 12
```

## Integration Points

The debug tracker is automatically initialized when `search_product()` is called and integrated into:

- **ShopifyJSONService** - Raw data extraction and conversion
- **LLMProductFilter** - Prefiltering and main filtering decisions  
- **URL validation** - Link and domain validation tracking
- **Store discovery** - Timing and error tracking
- **Final product selection** - LLM decision tracking

## Usage

### Automatic (Production)
Debug tracking is automatically enabled in the search pipeline. Each query creates its own debug folder.

### Manual Testing
```bash
cd backend
python test_debug_tracking.py
```

### Accessing Debug Data
```python
from app.utils.debug_tracker import init_debug_session, get_debug_tracker

# Initialize for a query
tracker = init_debug_session("women's boots")

# Use throughout your code
tracker = get_debug_tracker()
if tracker:
    tracker.track_error("Something went wrong", "context")

# Finalize when done
tracker.finalize_session(products_shown=5, links_shown=10)
```

## Debug Data Analysis

### Finding Specific Issues

1. **Why was a product filtered out?**
   - Check `shopify_prefiltered.json` vs `shopify_filtered.json`
   - Review `session_data.json` → `shopify_data.prefilter_reasons`

2. **Why did LLM reject products?**
   - Check `llm_selections.json` → `rejected` array
   - Review selection criteria used

3. **Why are certain stores not showing up?**
   - Check `session_data.json` → `url_validation.invalid_domains`
   - Review validation errors

4. **Performance bottlenecks?**
   - Check `SUMMARY.txt` timing breakdown
   - Review `session_data.json` → `timing.phases`

### Common Debug Scenarios

- **No products found**: Check `errors` array for fetch failures
- **Wrong products returned**: Review LLM selection criteria and prefilter decisions
- **Slow performance**: Check timing breakdown for bottlenecks
- **Missing stores**: Review invalid domains and validation errors

## Configuration

Debug artifacts are saved to `debug/` folder by default. To change:

```python
tracker = DebugTracker(query, debug_base_dir="custom_debug_path")
```

The system is designed to be lightweight and fail gracefully - if debug tracking has issues, it won't break the main search functionality. 