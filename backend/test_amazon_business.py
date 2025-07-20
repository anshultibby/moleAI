#!/usr/bin/env python3
"""
Test Amazon Business integration with Rye API
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the app directory to the path so we can import our modules
sys.path.append('app')

load_dotenv()

def test_amazon_business_domains():
    """Test Amazon Business domains after proper setup"""
    
    print("🧪 Testing Amazon Business Integration")
    print("=" * 50)
    
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
    
    # Amazon Business domains to test
    amazon_domains = [
        "amazon.com",
        "amazon.co.uk", 
        "amazon.ca",
        "business.amazon.com"
    ]
    
    print("Testing Amazon Business domains...")
    for domain in amazon_domains:
        print(f"\n🔍 Testing domain: {domain}")
        
        query = """
        query {
            productsByDomainV2(input: {domain: "%s"}, pagination: {limit: 3, offset: 0}) {
                id
                title
                price {
                    displayValue
                }
                isAvailable
            }
        }
        """ % domain
        
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json={"query": query},
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code == 200:
                if "errors" in result:
                    print(f"   ❌ GraphQL Error: {result['errors'][0]['message']}")
                else:
                    products = result.get("data", {}).get("productsByDomainV2", [])
                    if products:
                        print(f"   ✅ Found {len(products)} products!")
                        for product in products[:2]:
                            print(f"      - {product.get('title', 'N/A')}: {product.get('price', {}).get('displayValue', 'N/A')}")
                    else:
                        print(f"   ⚠️  No products found, but connection successful")
            else:
                print(f"   ❌ HTTP Error {response.status_code}: {result}")
                
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    
    print("\n" + "=" * 50)
    print("📋 RESULTS SUMMARY:")
    print("✅ If you see products: Amazon Business is connected!")
    print("⚠️  If no products but no errors: Connection works, inventory limited")
    print("❌ If you see errors: Amazon Business needs to be set up")
    print("\nNext steps if not working:")
    print("1. Verify Amazon Business account is created and verified")
    print("2. Check Rye console for Amazon Business connection options")
    print("3. Contact Rye support to enable Amazon Business access")

def test_specific_amazon_product():
    """Test fetching a specific Amazon product by URL"""
    
    print("\n🧪 Testing Specific Amazon Product Fetch")
    print("=" * 50)
    
    api_key = os.getenv("RYE_API_KEY")
    endpoint = "https://graphql.api.rye.com/v1/query"
    headers = {
        "Authorization": f"Basic {api_key}",
        "Rye-Shopper-IP": "127.0.0.1",
        "Content-Type": "application/json"
    }
    
    # Example Amazon product URL (replace with actual business product)
    test_url = "https://www.amazon.com/dp/B0B3PF8GWW"
    
    query = """
    mutation {
        requestProductByURL(input: {
            url: "%s",
            marketplace: AMAZON
        }) {
            productID
        }
    }
    """ % test_url
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json={"query": query},
            timeout=30
        )
        
        result = response.json()
        
        if response.status_code == 200 and "data" in result:
            product_id = result["data"]["requestProductByURL"]["productID"]
            print(f"✅ Successfully added Amazon product: {product_id}")
            return product_id
        else:
            print(f"❌ Failed to add product: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    test_amazon_business_domains()
    test_specific_amazon_product() 