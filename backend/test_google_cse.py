#!/usr/bin/env python3
"""
Test Google Custom Search Engine setup
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append('app')

from utils.google_discovery_service import GoogleDiscoveryService

load_dotenv()

def test_google_cse():
    """Test Google CSE configuration and basic search"""
    
    print("🧪 Testing Google Custom Search Engine Setup")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_CSE_ID")
    
    print(f"API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"Search Engine ID: {'✅ Set' if search_engine_id else '❌ Missing'}")
    
    if not api_key or not search_engine_id:
        print("\n❌ Setup incomplete!")
        print("Please add to your .env file:")
        print("GOOGLE_CSE_API_KEY=your_api_key_here")
        print("GOOGLE_CSE_ID=your_search_engine_id_here")
        return
    
    # Test the discovery service
    try:
        discovery = GoogleDiscoveryService()
        print("\n🔍 Testing store discovery for 'kids clothes'...")
        
        stores = discovery.discover_shopify_stores("kids clothes", max_results=5)
        
        if stores:
            print(f"✅ Found {len(stores)} Shopify stores!")
            for i, store in enumerate(stores, 1):
                print(f"  {i}. {store}")
                
                # Test store accessibility
                store_info = discovery.get_store_info(store)
                status = "✅ Accessible" if store_info['accessible'] else "❌ Not accessible"
                print(f"     Status: {status}")
        else:
            print("❌ No stores found. Check your CSE configuration:")
            print("   - Make sure you're searching *.myshopify.com")
            print("   - Try searching manually at https://cse.google.com/cse/")
            
    except Exception as e:
        print(f"❌ Error testing discovery: {e}")
        if "API key not valid" in str(e):
            print("   Your API key might be invalid or doesn't have Custom Search API enabled")
        elif "not found" in str(e):
            print("   Your Search Engine ID might be incorrect")

if __name__ == "__main__":
    test_google_cse() 