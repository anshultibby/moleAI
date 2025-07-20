"""
Rye API Service
Handles product search using Rye's GraphQL API for Amazon and Shopify products
"""

import os
import requests
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class RyeAPIService:
    def __init__(self, api_key: str = None, shopper_ip: str = None):
        self.api_key = api_key or os.getenv("RYE_API_KEY")
        self.shopper_ip = shopper_ip or os.getenv("RYE_SHOPPER_IP", "127.0.0.1")
        # Use production endpoint for better product availability
        self.base_url = "https://graphql.api.rye.com/v1/query"
        
        if not self.api_key:
            raise ValueError("RYE_API_KEY not found in environment variables")
        
        # Use Basic auth format as specified in Rye docs
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Rye-Shopper-IP": self.shopper_ip,
            "Content-Type": "application/json"
        }
    
    def search_products_by_domain(self, domain: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search for products from a specific domain using productsByDomainV2
        """
        query = """
        query ProductsByDomainV2($input: productsByDomainInput!, $pagination: OffsetPaginationInput!) {
            productsByDomainV2(input: $input, pagination: $pagination) {
                id
                title
                description
                price {
                    displayValue
                }
                images {
                    url
                }
                url
                isAvailable
                marketplace
                ... on ShopifyProduct {
                    vendor
                    productType
                }
            }
        }
        """
        
        variables = {
            "input": {"domain": domain},
            "pagination": {"limit": limit, "offset": offset}
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"GraphQL errors: {data['errors']}")
                    return []
                
                # productsByDomainV2 returns a list of products directly, not wrapped in an object
                products = data.get("data", {}).get("productsByDomainV2", [])
                
                # Transform to our expected format
                return self._transform_products(products)
            else:
                print(f"HTTP error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error searching products by domain: {str(e)}")
            return []
    
    def search_products_by_query(self, query: str, marketplaces: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for products using a text query across marketplaces
        Since Rye doesn't have a direct search by query endpoint, we'll search popular domains
        """
        if marketplaces is None:
            marketplaces = ["AMAZON", "SHOPIFY"]
        
        # Popular shopping domains to search
        domains_to_search = []
        
        # For now, Rye mainly supports specific Shopify stores that are onboarded
        # Amazon support appears limited in the staging environment
        if "SHOPIFY" in marketplaces:
            # We'll search some popular Shopify stores that work with Rye
            domains_to_search.extend([
                "shop.gymshark.com",
                "us.allbirds.com",
                "shop.bombas.com"
            ])
        
        # Amazon domains may not work in staging, but keeping for future use
        if "AMAZON" in marketplaces:
            domains_to_search.extend([
                # These may not work in staging environment
                "amazon.com",
                "amazon.co.uk", 
                "amazon.ca"
            ])
        
        all_products = []
        products_per_domain = max(1, limit // len(domains_to_search))
        
        for domain in domains_to_search:
            products = self.search_products_by_domain(domain, limit=products_per_domain)
            # Filter products that match our query
            filtered_products = [
                p for p in products 
                if query.lower() in p.get('product_name', '').lower() or 
                   query.lower() in p.get('description', '').lower()
            ]
            all_products.extend(filtered_products)
            
            if len(all_products) >= limit:
                break
        
        return all_products[:limit]
    
    def search_products(self, query: str, max_price: float = None, category: str = None, 
                       marketplaces: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Main search method that matches the expected interface from gemini_tools_converter
        """
        if marketplaces is None:
            marketplaces = ["AMAZON", "SHOPIFY"]
        
        # Use the query-based search
        products = self.search_products_by_query(query, marketplaces, limit)
        
        # Apply price filter if specified
        if max_price:
            products = [p for p in products if p.get('price_value', float('inf')) <= max_price]
        
        return products
    
    def get_product_by_id(self, product_id: str, marketplace: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed product information by ID
        """
        query = """
        query ProductByID($input: ProductByIDInput!) {
            productByID(input: $input) {
                id
                title
                description
                price {
                    value
                    currency
                }
                images {
                    url
                }
                url
                store {
                    ... on AmazonStore {
                        store
                        name
                    }
                    ... on ShopifyStore {
                        store
                        name
                    }
                }
                marketplace
            }
        }
        """
        
        variables = {
            "input": {
                "id": product_id,
                "marketplace": marketplace
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"GraphQL errors: {data['errors']}")
                    return None
                
                product = data.get("data", {}).get("productByID")
                if product:
                    return self._transform_product(product)
                
            return None
                
        except Exception as e:
            print(f"Error getting product by ID: {str(e)}")
            return None
    
    def request_product_by_url(self, url: str, marketplace: str) -> Optional[str]:
        """
        Request a product to be added to Rye's inventory by URL
        Returns the product ID if successful
        """
        mutation = """
        mutation RequestProductByURL($input: RequestProductByURLInput!) {
            requestProductByURL(input: $input) {
                productID
                isQueued
            }
        }
        """
        
        variables = {
            "input": {
                "url": url,
                "marketplace": marketplace
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": mutation, "variables": variables}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"GraphQL errors: {data['errors']}")
                    return None
                
                result = data.get("data", {}).get("requestProductByURL", {})
                return result.get("productID")
                
            return None
                
        except Exception as e:
            print(f"Error requesting product by URL: {str(e)}")
            return None
    
    def _transform_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single Rye product to our expected format"""
        price_info = product.get("price", {})
        # Use displayValue from the API response
        price_display = price_info.get("displayValue", "$0.00")
        
        # Extract numeric value for filtering
        try:
            price_value = float(price_display.replace("$", "").replace(",", ""))
        except:
            price_value = 0
        
        images = product.get("images", [])
        image_url = images[0].get("url") if images else ""
        
        # Handle vendor info for Shopify products
        vendor = product.get("vendor", "")
        store_name = vendor if vendor else "Rye Store"
        
        return {
            "type": "product",
            "product_name": product.get("title", ""),
            "price": price_display,
            "price_value": price_value,  # For filtering
            "image_url": image_url,
            "product_url": product.get("url", ""),
            "description": product.get("description", ""),
            "store_name": store_name,
            "source": "rye_api",
            "marketplace": product.get("marketplace", "SHOPIFY"),
            "rye_product_id": product.get("id", ""),
            "is_available": product.get("isAvailable", False),
            "product_type": product.get("productType", "")
        }
    
    def _transform_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform multiple Rye products to our expected format"""
        return [self._transform_product(product) for product in products]


def search_products_with_rye(
    query: str, 
    api_key: str = None,
    shopper_ip: str = None,
    limit: int = 10,
    marketplaces: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to search for products using Rye API
    """
    try:
        service = RyeAPIService(api_key, shopper_ip)
        return service.search_products_by_query(query, marketplaces, limit)
    except Exception as e:
        print(f"Error in Rye product search: {str(e)}")
        return []


def search_products_by_domain_with_rye(
    domain: str,
    api_key: str = None,
    shopper_ip: str = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Convenience function to search products from a specific domain using Rye API
    """
    try:
        service = RyeAPIService(api_key, shopper_ip)
        return service.search_products_by_domain(domain, limit)
    except Exception as e:
        print(f"Error in Rye domain search: {str(e)}")
        return [] 