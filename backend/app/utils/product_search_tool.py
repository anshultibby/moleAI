"""Product search tool using Google CSE and Shopify JSON"""

import json
from typing import List, Dict, Any
from .hybrid_search_service import HybridSearchService

async def search_products(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for products using hybrid search service
    Returns list of validated product JSONs
    """
    # Use the hybrid search service which combines Google CSE and Shopify JSON
    search_service = HybridSearchService()
    
    # Search for products
    search_result = await search_service.search(
        query=query,
        max_results=max_results,
        include_amazon=False  # Stick to Shopify for now
    )
    
    return search_result.products

def create_product_search_tool():
    """Create a Tool instance for product search"""
    from ..tools import Tool
    
    def sync_product_search(**kwargs):
        """Synchronous wrapper for async product search"""
        import asyncio
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 10)
        
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        products = loop.run_until_complete(
            search_products(query, max_results)
        )
        
        # Format results for agent
        return json.dumps({
            "products": products,
            "total_found": len(products),
            "query": query
        }, indent=2)
    
    return Tool(
        name="search_products",
        description="Search for products across validated e-commerce sites using Google CSE and Shopify JSON",
        function=sync_product_search,
        parameters={
            "query": {
                "type": "string",
                "description": "Product search query",
                "required": True
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of products to return",
                "required": False
            }
        }
    ) 