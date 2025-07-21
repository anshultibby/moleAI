#!/usr/bin/env python3
"""
Test Debug Tracking System
Demonstrates how debug artifacts are saved per query
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.debug_tracker import init_debug_session, get_debug_tracker, finalize_debug_session
from app.utils.hybrid_search_service import shopify_search


async def test_debug_tracking():
    """Test the debug tracking system with a real search query"""
    
    # Test query
    test_query = "black leather jacket women"
    
    print("🧪 Testing Debug Tracking System")
    print(f"Query: '{test_query}'")
    print("=" * 50)
    
    # Initialize debug session
    debug_tracker = init_debug_session(test_query)
    
    # Simulate search phases with timing
    debug_tracker.start_timing_phase("search_preparation")
    
    # Add some mock prefiltering decisions
    mock_products = [
        {"title": "Black Leather Jacket", "variants": [{"price": "89.99"}]},
        {"title": "Red Sweater", "variants": [{"price": "45.00"}]},
        {"title": "Women's Leather Coat", "variants": [{"price": "120.00"}]}
    ]
    
    # Track prefiltering (keeping relevant, removing irrelevant)
    debug_tracker.track_prefilter_decision(mock_products[0], "Matches query exactly", "kept")
    debug_tracker.track_prefilter_decision(mock_products[1], "Wrong category (sweater vs jacket)", "removed") 
    debug_tracker.track_prefilter_decision(mock_products[2], "Close match - leather coat", "kept")
    
    debug_tracker.end_timing_phase("search_preparation")
    
    # Simulate actual search
    debug_tracker.start_timing_phase("shopify_search")
    try:
        print("🔍 Running actual Shopify search...")
        products = await shopify_search(test_query, max_results=5)
        print(f"✅ Found {len(products)} products")
        
        # Track search results
        debug_tracker.track_search_results("shopify_json", len(products), 2.5)
        
        # Simulate some invalid URLs during link validation
        debug_tracker.track_invalid_url("http://invalid-store.com", "Connection timeout", "domain")
        debug_tracker.track_invalid_url("https://badscheme.ftp/store", "Invalid scheme: ftp", "link")
        debug_tracker.track_validation_error("https://broken-url", "DNS resolution failed")
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        debug_tracker.track_error(str(e), "shopify_search")
    
    debug_tracker.end_timing_phase("shopify_search")
    
    # Simulate LLM selection decisions
    debug_tracker.start_timing_phase("llm_selection")
    
    selected_products = [
        {
            "name": "Premium Black Leather Jacket",
            "price": "$129.99",
            "store": "Fashion Store",
            "reasoning": "High quality leather, matches query perfectly"
        },
        {
            "name": "Women's Motorcycle Jacket", 
            "price": "$89.99",
            "store": "Rider Gear",
            "reasoning": "Good price point, authentic leather"
        }
    ]
    
    rejected_products = [
        {
            "name": "Synthetic Jacket",
            "price": "$49.99", 
            "rejection_reason": "Not real leather as requested"
        }
    ]
    
    criteria = [
        "Must be genuine leather",
        "Designed for women",
        "Black color as specified", 
        "Reasonable price under $150"
    ]
    
    debug_tracker.track_llm_selection(selected_products, criteria, rejected_products)
    debug_tracker.end_timing_phase("llm_selection")
    
    # Track some additional filtering decisions
    for product in selected_products:
        debug_tracker.track_filter_decision(product, "Passed all criteria", "kept")
    
    for product in rejected_products:
        debug_tracker.track_filter_decision(product, product["rejection_reason"], "removed")
    
    # Finalize the debug session
    debug_tracker.finalize_session(len(selected_products), 15)  # 2 products shown, 15 links shown
    
    print("\n🎉 Debug tracking complete!")
    print(f"📁 Debug artifacts saved to: {debug_tracker.debug_dir}")
    print("\nFiles created:")
    print("- session_data.json (complete session data)")
    print("- shopify_raw_sample.json (raw Shopify data sample)")
    print("- shopify_prefiltered.json (after prefiltering)")
    print("- shopify_filtered.json (final filtered results)")
    print("- llm_selections.json (LLM decision details)")
    print("- SUMMARY.txt (human-readable summary)")
    

if __name__ == "__main__":
    asyncio.run(test_debug_tracking()) 