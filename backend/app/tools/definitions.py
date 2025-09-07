"""Tool function definitions - Define your functions here to convert them to tools"""

from typing import Optional, List, Dict, Any
from app.tools import tool
from app.modules.serp import search_jina, SearchError
import uuid


@tool(
    name="search_web_with_content",
    description="Search the web using Jina AI and return results with full page content in markdown format."
)
def search_web_with_content(
    query: str,
    num_results: int = 3,
    provider: str = "google"
) -> Dict[str, Any]:
    try:
        if not query or not query.strip():
            return {"error": "Query cannot be empty"}
        
        # Cap num_results at 3
        if num_results < 1 or num_results > 3:
            return {"error": "num_results must be between 1 and 3"}
        
        # Use the comprehensive search function that reads full content
        results = search_jina(
            query=query.strip(),
            num_results=num_results,
            provider=provider,
            read_content=True,
            respond_with="markdown",
            with_links_summary=True,
            with_images_summary=True,
            with_generated_alt=True
        )
        
        return results
        
    except SearchError as e:
        return {"error": f"Search error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@tool(
    name="display_items",
    description="""Display a curated list of products/items in the product panel. Use this to show specific product recommendations to the user.

Each item in the list should be a dictionary with these fields:
- product_name (required): The name/title of the product (string)
- price (required): The price as a string, e.g. "29.99", "$45.00", "€35.50" (string)
- store (required): The store/brand name, e.g. "Zara", "H&M", "Amazon" (string)
- image_url (optional): Direct URL to product image (string)
- product_url (optional): Direct link to the product page for purchasing (string)
- description (optional): Brief product description or details (string)
- currency (optional): Currency code like "USD", "EUR", "GBP" - defaults to "USD" (string)
- category (optional): Product category like "dress", "shoes", "jacket" (string)

Example usage:
display_items([
    {
        "product_name": "Classic White Button Shirt",
        "price": "49.99",
        "store": "Zara",
        "currency": "USD",
        "image_url": "https://example.com/shirt.jpg",
        "product_url": "https://zara.com/shirt-123",
        "description": "Cotton blend button-up shirt",
        "category": "shirt"
    }
])"""
)
def display_items(
    items: List[Dict[str, Any]],
    title: Optional[str] = None
) -> Dict[str, Any]:
    try:
        if not items:
            return {"error": "Items list cannot be empty"}
        
        processed_items = []
        
        for i, item in enumerate(items):
            # Validate required fields
            product_name = item.get('product_name') or item.get('name')
            price = item.get('price')
            store = item.get('store') or item.get('store_name')
            
            if not product_name:
                return {"error": f"Item {i+1} missing required field: product_name or name"}
            if not price:
                return {"error": f"Item {i+1} missing required field: price"}
            if not store:
                return {"error": f"Item {i+1} missing required field: store or store_name"}
            
            # Generate unique ID if not provided
            item_id = item.get('id')
            if not item_id:
                # Create ID from store and product name
                clean_store = str(store).lower().replace(' ', '-').replace('&', 'and')
                clean_name = str(product_name).lower().replace(' ', '-')
                item_id = f"{clean_store}-{clean_name}-{str(uuid.uuid4())[:8]}"
            
            # Normalize the item to match frontend Product interface
            processed_item = {
                "id": item_id,
                "product_name": str(product_name),
                "name": str(product_name),  # Alternative field
                "price": str(price),
                "currency": item.get('currency', 'USD'),
                "store": str(store),
                "store_name": str(store),  # Alternative field
                "image_url": item.get('image_url', ''),
                "product_url": item.get('product_url', ''),
                "description": item.get('description', ''),
                "category": item.get('category', ''),
                "type": "display_item"  # Mark as display item
            }
            
            processed_items.append(processed_item)
        
        return {
            "success": True,
            "title": title,
            "items": processed_items,
            "count": len(processed_items),
            "message": f"Successfully prepared {len(processed_items)} items for display"
        }
        
    except Exception as e:
        return {"error": f"Error processing items: {str(e)}"}