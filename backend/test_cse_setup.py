#!/usr/bin/env python3
"""
Test Google Custom Search Engine configuration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_cse_credentials():
    """Test if CSE credentials are configured"""
    
    print("🔧 Testing Google CSE Configuration")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_CSE_ID")
    
    print("1. Checking environment variables:")
    print(f"   GOOGLE_CSE_API_KEY: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"   GOOGLE_CSE_ID: {'✅ Set' if search_engine_id else '❌ Missing'}")
    
    if not api_key or not search_engine_id:
        print("\n❌ Missing credentials!")
        print("\nTo fix this:")
        print("1. Create a Google Custom Search Engine at: https://cse.google.com/cse/")
        print("2. Configure it to search *.myshopify.com")
        print("3. Get API key from Google Cloud Console")
        print("4. Add both to your .env file:")
        print("   GOOGLE_CSE_API_KEY=your_api_key_here")
        print("   GOOGLE_CSE_ID=your_search_engine_id_here")
        return False
    
    return True

def test_cse_connection():
    """Test actual CSE connection"""
    
    print("\n2. Testing CSE connection:")
    
    try:
        # Add the app directory to the path
        sys.path.append('app')
        from app.utils.google_discovery_service import GoogleDiscoveryService
        
        service = GoogleDiscoveryService()
        print("   ✅ Service initialized successfully")
        
        # Test a simple search
        print("   🔍 Testing search with 'shoes'...")
        
        # Test just the search query method to see raw results
        raw_domains = service._search_query("shoes site:myshopify.com", max_results=3)
        
        print(f"   📊 Raw CSE results: {len(raw_domains)} domains")
        
        if raw_domains:
            print("   ✅ CSE is working!")
            print("   Sample domains found:")
            for i, domain in enumerate(list(raw_domains)[:3], 1):
                print(f"      {i}. {domain}")
        else:
            print("   ⚠️  No results found")
            print("\n🔧 Possible CSE configuration issues:")
            print("   1. Make sure your CSE includes: *.myshopify.com")
            print("   2. Enable 'Search the entire web'")
            print("   3. Check if you've hit the daily quota (100 queries/day)")
            
    except ValueError as e:
        if "required in environment" in str(e):
            print("   ❌ Missing environment variables")
            return False
        else:
            print(f"   ❌ Configuration error: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        
        if "quota" in str(e).lower():
            print("   💡 This might be a quota issue - CSE has 100 queries/day limit")
        elif "key" in str(e).lower():
            print("   💡 This might be an API key issue")
        elif "cx" in str(e).lower():
            print("   💡 This might be a Search Engine ID issue")
            
        return False
    
    return True

def suggest_cse_configuration():
    """Suggest CSE configuration"""
    
    print("\n📋 Recommended CSE Configuration:")
    print("-" * 40)
    print("Sites to search:")
    print("   *.myshopify.com")
    print("   *.myshopify.com/*")
    print("   myshopify.com")
    
    print("\nSettings:")
    print("   ✅ Search the entire web: Enabled")
    print("   ✅ Image search: Enabled") 
    print("   ✅ SafeSearch: Moderate")
    print("   🌍 Language: English")
    print("   🏳️ Country: United States (or your target)")
    
    print("\nFor testing, try these search terms in your CSE:")
    print("   - shoes site:myshopify.com")
    print("   - clothing site:myshopify.com")
    print("   - accessories site:myshopify.com")

def main():
    """Run CSE setup tests"""
    
    print("🔗 Google Custom Search Engine Setup Test")
    print("=" * 50)
    
    # Test credentials
    if not test_cse_credentials():
        suggest_cse_configuration()
        return
    
    # Test connection
    if not test_cse_connection():
        suggest_cse_configuration()
        return
    
    print("\n🎉 CSE Configuration Test: PASSED!")
    print("Your Google Custom Search Engine is configured correctly.")

if __name__ == "__main__":
    main() 