"""Tool definitions using the decorator system"""

import json
from typing import Optional
from .tool_decorator import tool, ToolParameter
from .google_cse_service import GoogleCSEService
from .shopify_products_service import ShopifyProductsService
from .debug_logger import log_execution, debug_log
from datetime import datetime

@tool(
    name="find_stores",
    description="Find e-commerce stores that have a products.json endpoint",
    parameters={
        "query": ToolParameter(
            type="string",
            description="Product search query",
            required=True
        ),
        "max_results": ToolParameter(
            type="integer",
            description="Maximum number of stores to return",
            required=False
        )
    }
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
        return json.dumps({"stores": [], "query": query, "error": str(e)})

@tool(
    name="get_products",
    description="Get products from a store's products.json endpoint",
    parameters={
        "domain": ToolParameter(
            type="string",
            description="Store domain",
            required=True
        ),
        "query": ToolParameter(
            type="string",
            description="Optional query to filter products",
            required=False
        ),
        "limit": ToolParameter(
            type="integer",
            description="Maximum number of products to return",
            required=False
        )
    }
)
@log_execution
def fetch_products(domain: str, query: str = "", limit: int = 20) -> str:
    """Fetch products from a store's products.json"""
    debug_log(f"Starting product fetch from {domain} for query: {query}")
    
    if not domain:
        debug_log("No domain provided")
        return json.dumps({"error": "Store domain is required"})
    
    try:
        service = ShopifyProductsService()
        debug_log(f"Fetching products from {domain}...")
        products = service.search_products(domain, query, limit)
        
        # Format products to match frontend expectations
        formatted_products = []
        for p in products:
            product_id = f"{p.store_domain}-{p.title}".lower().replace(" ", "-").replace("/", "-").replace("&", "and")
            formatted_products.append({
                "product_name": p.title,
                "price": p.price,
                "store": p.store_domain,
                "image_url": p.image_url,
                "product_url": p.product_url,
                "description": p.description,
                "id": product_id
            })
        
        # Return in ChatResponse format
        response = {
            "response": f"Found {len(formatted_products)} products from {domain}" + (f" matching '{query}'" if query else ""),
            "timestamp": datetime.now().isoformat(),
            "deals_found": formatted_products
        }
        
        debug_log(f"Found {len(formatted_products)} products")
        return json.dumps(response, indent=2)
        
    except Exception as e:
        debug_log(f"Error in fetch_products: {str(e)}")
        return json.dumps({
            "response": f"Error fetching products from {domain}: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "deals_found": []
        })

@tool(
    name="add_product",
    description="Add a product to be displayed in the frontend products panel",
    parameters={
        "product_name": ToolParameter(
            type="string",
            description="Name/title of the product",
            required=True
        ),
        "price": ToolParameter(
            type="string",
            description="Price of the product (include currency symbol)",
            required=True
        ),
        "store": ToolParameter(
            type="string",
            description="Name of the store selling the product",
            required=True
        ),
        "image_url": ToolParameter(
            type="string",
            description="URL of the product image",
            required=False
        ),
        "product_url": ToolParameter(
            type="string",
            description="URL where the product can be purchased",
            required=False
        ),
        "description": ToolParameter(
            type="string",
            description="Description of the product",
            required=False
        ),
        "category": ToolParameter(
            type="string",
            description="Category of the product",
            required=False
        )
    }
)
@log_execution
def add_product(
    product_name: str,
    price: str,
    store: str,
    image_url: Optional[str] = None,
    product_url: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    """Add a product to be displayed in the frontend products panel"""
    debug_log(f"Adding product: {product_name} from {store}")
    
    try:
        # Create product object matching frontend Product interface
        product = {
            "product_name": product_name,
            "price": price,
            "store": store,
            "image_url": image_url,
            "product_url": product_url,
            "description": description,
            "category": category,
            "id": f"{store}-{product_name}".lower().replace(" ", "-").replace("/", "-").replace("&", "and")
        }
        
        # Return in ChatResponse format with deals_found array
        response = {
            "response": f"Found: {product_name} from {store} for {price}",
            "timestamp": datetime.now().isoformat(),
            "deals_found": [product]
        }
        
        debug_log(f"Product added successfully: {product['id']}")
        return json.dumps(response, indent=2)
        
    except Exception as e:
        debug_log(f"Error in add_product: {str(e)}")
        return json.dumps({
            "error": str(e)
        })

def get_tools():
    """Get all tools for the agent"""
    debug_log("Creating tools...")
    from .tool_decorator import create_tool
    tools = [
        create_tool(discover_stores),
        create_tool(fetch_products),
        create_tool(add_product)  # Add the new tool
    ]
    debug_log(f"Created {len(tools)} tools")
    return tools 