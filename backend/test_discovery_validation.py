#!/usr/bin/env python3
"""
Test discovery validation to ensure broken domains are filtered out
"""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

from app.utils.google_discovery_service import GoogleDiscoveryService

def test_discovery_validation():
    """Test that discovery filters out broken domains"""
    
    print("🧪 Testing Discovery Domain Validation")
    print("=" * 60)
    
    # Test the validation function directly with known broken domains
    service = GoogleDiscoveryService()
    
    # Mock candidate domains including the problematic one
    candidate_domains = [
        "shop.gymshark.com",           # Should work
        "us.lovefitwear.com",          # Broken domain from your example
        "example.myshopify.com",       # Should be accessible or not
        "test-store.myshopify.com",    # Likely doesn't exist
        "shop.allbirds.com",           # Should work
        "fake-broken-store.myshopify.com",  # Definitely doesn't exist
    ]
    
    print(f"Testing validation with candidate domains:")
    for i, domain in enumerate(candidate_domains, 1):
        print(f"   {i}. {domain}")
    
    print(f"\n🔍 Running validation...")
    
    try:
        validated_domains = service._validate_discovered_domains(candidate_domains, max_results=10)
        
        print(f"\n📊 Results:")
        print(f"   📥 Input domains: {len(candidate_domains)}")
        print(f"   ✅ Validated domains: {len(validated_domains)}")
        print(f"   🚫 Filtered out: {len(candidate_domains) - len(validated_domains)}")
        
        print(f"\n✅ Accessible domains:")
        for i, domain in enumerate(validated_domains, 1):
            print(f"   {i}. {domain}")
        
        # Check if the problematic domain was filtered out
        if "us.lovefitwear.com" in validated_domains:
            print(f"\n❌ PROBLEM: us.lovefitwear.com was NOT filtered out!")
        else:
            print(f"\n✅ SUCCESS: us.lovefitwear.com was correctly filtered out!")
        
        # Test that we got at least some working domains
        working_domains = [d for d in validated_domains if d in ["shop.gymshark.com", "shop.allbirds.com"]]
        if working_domains:
            print(f"✅ SUCCESS: Found {len(working_domains)} known working domains")
        else:
            print(f"⚠️  WARNING: No known working domains found (might be network issue)")
            
    except Exception as e:
        print(f"❌ Validation test failed: {e}")

def test_discovery_integration():
    """Test the full discovery process"""
    
    print(f"\n" + "=" * 60)
    print(f"🔍 Testing Full Discovery Integration")
    print("=" * 60)
    
    try:
        service = GoogleDiscoveryService()
        
        # Test discovery with a simple query
        print(f"Running discovery for 'black leggings' (limited results for testing)...")
        
        discovered_domains = service.discover_shopify_stores("black leggings", max_results=5)
        
        print(f"\n📊 Discovery Results:")
        print(f"   🎯 Domains found: {len(discovered_domains)}")
        
        if discovered_domains:
            print(f"   Domains:")
            for i, domain in enumerate(discovered_domains, 1):
                print(f"   {i}. {domain}")
            
            # Verify none of the known broken domains made it through
            broken_domains = ["us.lovefitwear.com", "example.com", "test.com"]
            found_broken = [d for d in discovered_domains if d in broken_domains]
            
            if found_broken:
                print(f"\n❌ PROBLEM: Found broken domains: {found_broken}")
            else:
                print(f"\n✅ SUCCESS: No known broken domains found")
        else:
            print(f"   ⚠️  No domains discovered (could be API limits or network issue)")
            
    except Exception as e:
        print(f"❌ Discovery integration test failed: {e}")
        
        # If Google CSE is not configured, that's expected
        if "GOOGLE_CSE" in str(e):
            print(f"   (This is expected if Google CSE API keys are not configured)")

def main():
    """Run discovery validation tests"""
    
    print("🔗 Discovery Domain Validation Test Suite")
    print("=" * 60)
    
    # Test domain validation
    test_discovery_validation()
    
    # Test full discovery process
    test_discovery_integration()
    
    print(f"\n📋 Summary:")
    print(f"   The discovery service now validates domains during discovery")
    print(f"   Broken domains like 'us.lovefitwear.com' should be filtered out")
    print(f"   Only accessible Shopify stores will be returned for product search")
    print(f"   This prevents broken product URLs from reaching users")

if __name__ == "__main__":
    main() 