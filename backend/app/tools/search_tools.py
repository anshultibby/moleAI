"""Store discovery and product fetching tools"""

import json
from typing import Optional
from .decorator import tool
from ..utils.google_cse_service import GoogleCSEService
from ..utils.shopify_products_service import ShopifyProductsService
from ..utils.debug_logger import log_execution, debug_log
from datetime import datetime


@tool(
    name="find_stores",
    description="Discover e-commerce stores that sell products related to your query. Use this first to find stores, then use fetch_products to get products from specific stores."
)
@log_execution
def discover_stores(query: str, max_results: int = 5) -> str:
    """Find stores with products.json matching the query"""
    debug_log(f"Starting store discovery for: {query}")
    try:
        service = GoogleCSEService()
        stores = service.discover_stores(query, max_results)
        
        result = {
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
        }
        debug_log(f"Found {len(result['stores'])} stores")
        return json.dumps(result, indent=2)
    except Exception as e:
        debug_log(f"Error in discover_stores: {str(e)}")
        return json.dumps({"error": str(e), "stores": []})


@tool(
    name="fetch_products", 
    description="Search for products from a specific store. Returns product data for review. Use add_product tool to display selected products to the user."
)
@log_execution  
def fetch_products(domain: str, query: Optional[str] = None, max_results: int = 10) -> str:
    """Fetch products from a store's products.json"""
    debug_log(f"Fetching products from {domain}, query: {query}")
    try:
        service = ShopifyProductsService()
        if query:
            # Use search_products when a query is provided
            products = service.search_products(domain, query, max_results)
        else:
            # Use fetch_products when no query (just browsing all products)
            products = service.fetch_products(domain, max_results)
        
        result = {
            "products": [
                {
                    "title": product.title,
                    "price": product.price,
                    "image_url": product.image_url,
                    "product_url": product.product_url,
                    "description": product.description,
                    "store": domain
                }
                for product in products
            ],
            "domain": domain,
            "query": query,
            "total_found": len(products)
        }
        
        debug_log(f"Fetched {len(products)} products from {domain}")
        return json.dumps(result, indent=2)
    except Exception as e:
        debug_log(f"Error fetching products from {domain}: {str(e)}")
        return json.dumps({"error": str(e), "products": []})


# Helper functions for the tools
def format_store_info(store):
    """Format store information for display"""
    return {
        "domain": store.domain,
        "title": store.title,
        "description": store.description,
        "products_available": store.has_products_json
    }

def format_product_info(product, store_domain):
    """Format product information for display"""
    return {
        "name": product.title,
        "price": product.price,
        "store": store_domain,
        "image": product.image_url,
        "url": product.product_url,
        "description": product.description
    } 