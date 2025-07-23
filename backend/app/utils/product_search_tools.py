"""Tools for store discovery and product search"""

import json
from typing import List, Dict, Any
from .google_cse_service import GoogleCSEService
from .shopify_products_service import ShopifyProductsService

def create_tools() -> List[Dict[str, Any]]:
    """Create the store discovery and product fetch tools"""
    from ..modules.agent import Tool
    
    # Store Discovery Tool
    def discover_stores(**kwargs):
        """Find stores with products.json matching the query"""
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)
        
        service = GoogleCSEService()
        stores = service.discover_stores(query, max_results)
        
        return json.dumps({
            "stores": [
                {
                    "domain": store.domain,
                    "title": store.title,
                    "description": store.description,
                    "has_products": store.has_products_json
                }
                for store in stores
            ],
            "query": query
        }, indent=2)
    
    store_tool = Tool(
        name="find_stores",
        description="Find e-commerce stores that have a products.json endpoint",
        function=discover_stores,
        parameters={
            "query": {
                "type": "string",
                "description": "Product search query",
                "required": True
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of stores to return",
                "required": False
            }
        }
    )
    
    # Product Fetch Tool
    def fetch_products(**kwargs):
        """Fetch products from a store's products.json"""
        domain = kwargs.get("domain", "")
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 20)
        
        if not domain:
            return json.dumps({"error": "Store domain is required"})
        
        service = ShopifyProductsService()
        products = service.search_products(domain, query, limit)
        
        return json.dumps({
            "products": [
                {
                    "title": p.title,
                    "description": p.description,
                    "price": p.price,
                    "url": p.product_url,
                    "image": p.image_url,
                    "store": p.store_domain
                }
                for p in products
            ],
            "store": domain,
            "query": query
        }, indent=2)
    
    product_tool = Tool(
        name="get_products",
        description="Get products from a store's products.json endpoint",
        function=fetch_products,
        parameters={
            "domain": {
                "type": "string",
                "description": "Store domain",
                "required": True
            },
            "query": {
                "type": "string",
                "description": "Optional query to filter products",
                "required": False
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of products to return",
                "required": False
            }
        }
    )
    
    return [store_tool, product_tool] 