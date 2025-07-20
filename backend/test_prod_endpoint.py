#!/usr/bin/env python3
"""
Test production Rye API endpoint to see if Amazon domains work
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_prod_endpoints():
    """Test both Amazon and Shopify domains with production endpoint"""
    
    api_key = os.getenv("RYE_API_KEY")
    if not api_key:
        print("❌ RYE_API_KEY not found")
        return
    
    endpoint = "https://graphql.api.rye.com/v1/query"
    headers = {
        "Authorization": f"Basic {api_key}",
        "Rye-Shopper-IP": "127.0.0.1",
        "Content-Type": "application/json"
    }
    
    domains_to_test = [
        ("amazon.com", "Amazon"),
        ("shop.gymshark.com", "Gymshark (Shopify)")
    ]
    
    for domain, name in domains_to_test:
        print(f"🧪 Testing {name} ({domain})...")
        
        query = """
        query {
            productsByDomainV2(input: {domain: "%s"}, pagination: {limit: 2, offset: 0}) {
                id
                title
                price {
                    displayValue
                }
                isAvailable
                marketplace
            }
        }
        """ % domain
        
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json={"query": query}
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    error_msg = data["errors"][0]["message"]
                    print(f"   ❌ Error: {error_msg[:100]}...")
                else:
                    products = data.get("data", {}).get("productsByDomainV2", [])
                    if products:
                        print(f"   ✅ Found {len(products)} products!")
                        for i, product in enumerate(products, 1):
                            print(f"      {i}. {product['title'][:50]}... - {product['price']['displayValue']}")
                    else:
                        print("   ⚠️  No products returned")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()

if __name__ == "__main__":
    print("🚀 Testing Production Rye API Endpoint")
    print("=" * 50)
    test_prod_endpoints() 