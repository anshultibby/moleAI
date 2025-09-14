"""Tool function definitions - Define your functions here to convert them to tools"""

from typing import Optional, List, Dict, Any, Union
from app.tools import tool
from app.modules.serp import search_web, SearchError
from app.modules.direct_scraper import DirectScraper, DirectScraperError
from app.models.resource import (
    Resource,
    ResourceMetadata
)
from app.modules.product_extractor import ProductExtractor
from app.models.product import Product

import uuid
import re
import json
import asyncio
from datetime import datetime


class StreamHelper:
    """Centralized helper for tool streaming functionality"""
    
    def __init__(self, stream_callback, tool_name: str):
        self.stream_callback = stream_callback
        self.tool_name = tool_name
    
    def progress(self, message: str, **progress_data):
        """Emit a progress update"""
        if self.stream_callback:
            self.stream_callback(self.tool_name, "progress", message=message, progress=progress_data)
    
    def completed(self, message: str, result_data: Dict = None, **progress_data):
        """Emit a completion update"""
        if self.stream_callback:
            result_json = json.dumps(result_data) if result_data else None
            self.stream_callback(self.tool_name, "completed", 
                               message=message, 
                               progress=progress_data,
                               result=result_json)
    
    def error(self, message: str, **progress_data):
        """Emit an error update"""
        if self.stream_callback:
            self.stream_callback(self.tool_name, "error", message=message, progress=progress_data)
    
    @classmethod
    def for_search(cls, stream_callback, query: str, num_results: int, results: List[Dict] = None, error_msg: str = None):
        """Factory method for search tool streaming"""
        helper = cls(stream_callback, "search_web_tool")
        
        if results is not None:
            # Success case with results
            stores = []
            for result in results:
                stores.append({
                    "title": result.get('title', 'Store'),
                    "url": result.get('url', '')
                })
            
            result_data = {
                "query": query,
                "results": stores
            }
            
            message = f"Found {len(stores)} stores" if stores else "No results found"
            helper.completed(message, result_data, query=query, num_results=num_results)
        else:
            # Error case or empty results
            result_data = {
                "query": query,
                "results": []
            }
            
            message = error_msg or "No results found"
            helper.completed(message, result_data, query=query, num_results=num_results)
    
    @classmethod
    def for_scraping(cls, stream_callback, tool_name: str = "scrape_website"):
        """Factory method for scraping tool streaming"""
        return cls(stream_callback, tool_name)



@tool(
    name="search_web_tool",
    description="""Search the web to get SERP results using broad, general queries.
    
    IMPORTANT: Use natural, general search queries without site restrictions (no "site:" operators).
    Let Google's algorithm naturally surface the best results from various retailers.
    
    Examples:
    - Good: "trendy winter coats for women 2025"
    - Good: "midi dresses under $100"
    - Bad: "winter coats site:zara.com OR site:hm.com"
    - Bad: "dresses site:nordstrom.com"
    
    After getting search results, you can choose which diverse retailer links to scrape.
    Focus on the product attributes the user wants, not specific brands unless explicitly requested.
    """
)
def search_web_tool(
    query: str,
    num_results: int = 10,
    context_vars=None
) -> Dict[str, Any]:
    if not query or not query.strip():
        return {"error": "Query cannot be empty"}

    # Create stream helper
    stream_callback = context_vars.get('stream_callback') if context_vars else None
    streamer = StreamHelper(stream_callback, "search_web_tool")
    
    try:
        # Emit progress update
        streamer.progress(f"🔍 Searching the web for: {query}", query=query, num_results=num_results)

        results = search_web(
            query=query.strip(),
            num_results=num_results,
            provider="google"
        )
        
        # Emit completion update
        search_results = results.get('results', []) if isinstance(results, dict) else []
        StreamHelper.for_search(stream_callback, query, num_results, search_results)
        
        return results
        
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        StreamHelper.for_search(stream_callback, query, num_results, error_msg=error_msg)
        return {"error": error_msg}


@tool(
    name="extract_products",
    description="""Extract product information from e-commerce website URLs using advanced extraction methods.
    This tool scrapes product pages and automatically extracts structured product data including:
    - Product titles, prices, and currencies
    - Brand/vendor information
    - SKUs and product IDs
    - Product images and URLs
    
    Uses multiple extraction methods in priority order:
    1. Shopify Analytics (fast path) - extracts from analytics blob
    2. Atom Feed parsing - extracts from RSS/Atom feeds
    3. HTML Heuristics - extracts using CSS selectors and patterns
    
    Parameters:
    - urls: Dictionary where keys are meaningful resource names and values are URLs to scrape
           Example: {"zara_dresses": "https://zara.com/dresses", "hm_shirts": "https://hm.com/shirts"}
    - render_js: Whether to render JavaScript (default: True for dynamic content)
    - wait: Time to wait in milliseconds after page load (default: 2000ms)
    
    The tool stores both the raw scraped content as resources AND extracts structured product data.
    Use meaningful, succinct resource names that describe the products being extracted.
    Good examples: "zara_dresses", "amazon_laptops", "nike_shoes"
    """
)
async def extract_products(
    urls: Dict[str, str],
    render_js: bool = True,
    wait: int = 2000,
    context_vars=None
) -> str:
    if not urls:
        return "URLs cannot be empty"
    
    # Main extraction logic (now inline since function is async)
    resources = context_vars.get('resources')
    stream_callback = context_vars.get('stream_callback')
    streamer = StreamHelper.for_scraping(stream_callback)
    
    # Create progress callback for the extractor
    def progress_callback(message, current=None, total=None, status=None, url=None):
        streamer.progress(message, current=current, total=total, status=status, url=url)
    
    # Let ProductExtractor handle everything
    product_extractor = ProductExtractor()
    product_collections = await product_extractor.scrape_and_extract_multiple(
        urls=urls,
        render_js=render_js,
        wait=wait,
        progress_callback=progress_callback,
        conversation_id=context_vars.get('conversation_id')
    )
    
    # Store collections as resources
    total_products = 0
    
    for collection in product_collections:
        # Store ProductCollection directly using source_name as key
        resources[collection.source_name] = collection
        total_products += len(collection)
    
    # Send completion message
    sites_with_products = sum(1 for c in product_collections if len(c) > 0)
    if total_products > 0:
        message = f"Extracted {total_products} products from {sites_with_products} sites"
    else:
        message = f"No products found from {len(product_collections)} sites"
    
    streamer.completed(message, {
        "total_products_extracted": total_products,
        "sites_with_products": sites_with_products,
        "total_sites": len(product_collections)
    })
    
    # Return summary using get_resource for each collection
    if total_products > 0:
        summary_parts = [f"🛍️ Extracted {total_products} products total\n", "Summary of extracted products:\n"]
        
        for collection in product_collections:
            if len(collection) > 0:  # Only show collections with products
                resource_summary = get_resource(
                    resource_id=collection.source_name,
                    limit=5,
                    summary=True,
                    context_vars=context_vars
                )
                summary_parts.append(f"\n{resource_summary}")
        
        return "\n".join(summary_parts)
    else:
        return "No products were extracted from the provided URLs."


def get_resource_content(resource_id: str, context_vars) -> tuple[str, Optional[str]]:
    """Helper to get resource content with validation. Returns (content, error_message)"""
    resources = context_vars.get('resources')
    collection = resources.get(resource_id)
    
    if not collection:
        return None, f"Resource with ID '{resource_id}' not found"
    
    if not collection.products:
        return None, f"Resource '{resource_id}' has no products to search"
    
    # Return JSON representation of the collection for text-based operations
    return collection.to_json(), None


@tool(
    name="get_resource",
    description="""Get a product collection resource by its name. 
    Returns the product collection data using the collection's get_products method.

    Parameters:
    - resource_id: The ID of the resource to get
    - limit: Maximum number of products to show (default: 5)
    - max_price: Maximum price filter - only show products under this price (optional)
    - summary: If True, returns just product names; if False, returns full product details (default: True)
    - context_vars: The context variables to use

    Returns JSON with collection metadata and filtered products.
    """
)
def get_resource(
    resource_id: str,
    limit: int = 5,
    max_price: float = None,
    summary: bool = True,
    context_vars=None
) -> str:
    resources = context_vars.get('resources')
    collection = resources.get(resource_id)
    if not collection:
        return f"Resource with ID '{resource_id}' not found"
    
    result = collection.get_products(limit=limit, summary=summary, max_price=max_price)
    return json.dumps(result, indent=2)


@tool(
    name="list_resources",
    description="""List all product collection resources that have been created so far.
    Returns a summary of all product collections with their metadata.
    """
)
def list_resources(context_vars=None) -> str:
    resources = context_vars.get('resources')
    if not resources:
        return "No product collections found"
    
    summary_lines = [f"Found {len(resources)} product collection(s):\n"]
    
    for name, collection in resources.items():
        result = collection.get_products(limit=2, summary=True)
        summary_lines.append(result)
    return json.dumps(summary_lines, indent=2)


@tool(
    name="display_items",
    description="""Display products that will stream to the user in real-time as they are processed. 
    Products appear immediately as each one is processed, creating a dynamic streaming experience.
    This is a very important tool to call as it makes for a very delightful experience for the user, our main goal is to keep the user engaged.

This tool accepts either Product instances from app.models.product.Product OR dictionaries with product data.

The Product class has these fields:
- title: Product name/title
- price: Product price amount (float)
- currency: Price currency (USD, EUR, etc.)
- vendor: Brand or vendor name (used as store name)
- sku: Stock Keeping Unit
- image_url: Primary product image URL
- product_id: Unique product identifier
- variant_id: Unique variant identifier
- product_url: URL to the product page

Example usage:
display_items([product1, product2, product3])
display_items([{"title": "Product Name", "price": 99.99, "currency": "USD", "vendor": "Store Name", "image_url": "..."}])

Products will appear one by one in real-time as they are processed, not all at once at the end."""
)
def display_items(
    items: List[Union[Product, Dict[str, Any]]],
    title: Optional[str] = None,
    context_vars=None
) -> Dict[str, Any]:
    if not items:
        return {"error": "Items list cannot be empty"}
    
    processed_items = []
    
    for i, item in enumerate(items):
        # Convert dict to Product instance if needed
        if isinstance(item, dict):
            try:
                product = Product(**item)
            except Exception as e:
                return {"error": f"Item {i+1} could not be converted to Product: {str(e)}"}
        elif isinstance(item, Product):
            product = item
        else:
            return {"error": f"Item {i+1} must be a Product instance or dict, got {type(item)}"}
        
        # Convert Product to dict using Pydantic and map to frontend format
        product_dict = product.model_dump()
        
        # Generate unique ID
        clean_store = str(product.vendor or '').lower().replace(' ', '-').replace('&', 'and')[:20]
        clean_name = str(product.title or '').lower().replace(' ', '-')[:30]
        item_id = f"{clean_store}-{clean_name}-{str(uuid.uuid4())[:8]}"
        
        # Map to frontend Product interface format
        processed_item = {
            "id": item_id,
            "product_name": product.title or '',
            "name": product.title or '',  # Alternative name field
            "price": str(product.price or ''),
            "currency": product.currency or 'USD',
            "store": product.vendor or '',
            "store_name": product.vendor or '',  # Alternative store field
            "image_url": product.image_url or '',
            "product_url": product.product_url or '',
            "description": '',  # Product model doesn't have this field
            "category": '',     # Product model doesn't have this field
            "type": "streaming_product"
        }
        
        processed_items.append(processed_item)
    
    return {
        "success": True,
        "stream_products": True,
        "title": title or "Products Found",
        "items": processed_items,
        "count": len(processed_items),
        "message": f"Found {len(processed_items)} products"
    }


@tool(
    name="checklist",
    description="""Manage checklists with create, update, and get operations.
    
    Operations:
    - create: Create a new checklist with title and items
    - update: Mark checklist items as completed or uncompleted
    - get: Retrieve existing checklist
    
    The checklist is stored in the agent's context and automatically included in conversations.
    When a checklist exists, always include it and ask the user to mark completed items.
    
    Parameters:
    - operation: "create", "update", or "get"
    - title: Title for the checklist (required for create)
    - items: List of checklist items as strings (required for create)
    - item_updates: Dictionary mapping item indices to completion status for update
                   Example: {0: True, 2: False} marks first item complete, third incomplete
    """
)
def checklist(
    operation: str,
    title: str = None,
    items: List[str] = None,
    item_updates: Dict[int, bool] = None,
    context_vars=None
) -> str:
    if not operation or operation not in ["create", "update", "get"]:
        return "Error: operation must be 'create', 'update', or 'get'"
    
    agent = context_vars.get('agent')
    if not agent:
        return "Error: Agent context not available"
    
    if operation == "get":
        if agent.checklist:
            return f"Current checklist: {json.dumps(agent.checklist, indent=2)}"
        else:
            return "No checklist found"
    
    elif operation == "create":
        if not title or not items:
            return "Error: title and items are required for create operation"
        
        # Create new checklist
        agent.checklist = {
            "title": title,
            "items": [{"text": item, "completed": False} for item in items],
            "created_at": datetime.now().isoformat()
        }
        
        return f"Created checklist '{title}' with {len(items)} items"
    
    elif operation == "update":
        if not agent.checklist:
            return "Error: No existing checklist found to update"
        
        if not item_updates:
            return "Error: item_updates required for update operation"
        
        # Update checklist items
        for item_index, completed in item_updates.items():
            if 0 <= item_index < len(agent.checklist["items"]):
                agent.checklist["items"][item_index]["completed"] = completed
        
        agent.checklist["updated_at"] = datetime.now().isoformat()
        
        # Count completed items
        completed_count = sum(1 for item in agent.checklist["items"] if item["completed"])
        total_count = len(agent.checklist["items"])
        
        return f"Updated checklist: {completed_count}/{total_count} items completed"


