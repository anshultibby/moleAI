"""Tool function definitions - Define your functions here to convert them to tools"""

from typing import Optional, List, Dict, Any, Union
from app.tools import tool
from app.modules.serp import search_web
from app.modules.extractors.simple_extractor import extract_products_simple
from app.models.product import Product
from app.models.product_collection import ProductCollection
from app.models.chat.content import TextContent, ImageContent, VisionMultimodalContentItem, create_multimodal_product_content

import json
from datetime import datetime
from loguru import logger


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
    num_results: int = 5,
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
    description="""Extract product information from e-commerce websites using BrightData Web Unlocker API.
    
    WORKFLOW: 
    1. First use search_web_tool to find e-commerce URLs
    2. Extract the 'url' field from search results
    3. Pass those URLs to this tool as a list
    
    Automatic bot detection bypass with:
    - PerimeterX, Cloudflare, Datadome protection bypass
    - JavaScript rendering for SPAs (React, Vue, Next.js)
    - Residential proxy rotation
    - CAPTCHA solving
    - Cost: $1.50 per 1,000 requests
    
    Supports all modern e-commerce platforms:
    - Shopify stores
    - WooCommerce sites
    - Custom JavaScript SPAs
    - Bot-protected sites
    
    Extraction strategies (tries in order):
    1. Fast path: Extract all products from listing page ItemList JSON-LD (20x faster!)
    2. Fallback: Fetch individual product pages and extract from JSON-LD/Next.js/__NEXT_DATA__/meta tags
    
    Extracts:
    - Product names, prices, currencies
    - Brand/vendor information
    - SKUs and product IDs
    - Product images and URLs
    - Descriptions
    
    Parameters:
    - urls: List of collection/listing page URLs to scrape (REQUIRED - cannot be empty)
    - max_products: Maximum products per URL (default: 20)
    
    Works with: Hello Molly, Express.com, Fashion Nova, and 95%+ of e-commerce sites
    """
)
async def extract_products(
    urls: List[str],
    max_products: int = 20,
    context_vars=None
) -> str:
    if not urls or not isinstance(urls, list) or len(urls) == 0:
        return "Error: URLs list cannot be empty. You must provide a list of collection/listing page URLs to extract products from. Use search_web_tool first to find relevant e-commerce URLs, then pass those URLs to this tool."
    
    # Get context
    resources = context_vars.get('resources')
    stream_callback = context_vars.get('stream_callback')
    streamer = StreamHelper.for_scraping(stream_callback, "extract_products")
    
    try:
        # Start extraction
        streamer.progress(f"🔍 Extracting products from {len(urls)} URLs", total_urls=len(urls), max_products=max_products)
        
        # Use the BrightData API extractor (handles parallelization internally)
        from app.modules.extractors import extract_products_from_multiple_urls
        from app.models.product import Product
        
        # Extract from all URLs (parallelized internally)
        all_results = await extract_products_from_multiple_urls(
            urls=urls,
            max_products=max_products,
            progress_callback=lambda msg: streamer.progress(msg)
        )
        
        # Convert results to Product objects and store in resources
        all_products = []
        for url, result in all_results.items():
            if not result.get('success'):
                logger.warning(f"Failed to extract from {url}: {result.get('error')}")
                streamer.progress(f"❌ Failed: {url}")
                continue
            
            # Convert product dicts to Product model
            url_products = []
            for product_dict in result.get('products', []):
                try:
                    raw_price = product_dict.get('price', 0)
                    
                    core_product = Product(
                        product_name=product_dict.get('title', ''),
                        price=str(raw_price),
                        price_value=raw_price,
                        currency=product_dict.get('currency', 'USD'),
                        store=product_dict.get('brand', ''),
                        product_url=product_dict.get('product_url', ''),
                        image_url=product_dict.get('image_url', ''),
                        sku=product_dict.get('sku'),
                        description=product_dict.get('description', '')
                    )
                    url_products.append(core_product)
                except Exception as e:
                    logger.warning(f"Failed to convert product: {e}")
                    continue
            
            if url_products:
                all_products.extend(url_products)
                
                # Store as resource
                domain = url.split('//')[-1].split('/')[0]
                resource_name = f"products_from_{domain}"
                
                collection = ProductCollection(
                    source_name=resource_name,
                    source_url=url,
                    products=url_products,
                    extraction_method="brightdata_api"
                )
                resources[resource_name] = collection
                
                streamer.progress(f"✅ {domain}: {len(url_products)} products")
        
        # Store all products combined as a ProductCollection
        if all_products:
            combined_collection = ProductCollection(
                source_name="all_extracted_products",
                source_url=urls[0] if len(urls) == 1 else f"combined_from_{len(urls)}_urls",
                products=all_products,
                extraction_method="json_ld_schema_org"
            )
            resources["all_extracted_products"] = combined_collection
        
        # Send completion message
        if all_products:
            message = f"Extracted {len(all_products)} total products from {len(urls)} URLs"
            streamer.completed(message, {
                "total_products": len(all_products),
                "total_urls": len(urls),
                "resource_name": "all_extracted_products"
            })
            
            # Return summary
            summary_parts = [f"🛍️ Extracted {len(all_products)} total products from {len(urls)} URLs\n"]
            summary_parts.append("Resources created:")
            
            # Show per-URL breakdown
            for url in urls:
                domain = url.split('//')[-1].split('/')[0]
                resource_name = f"products_from_{domain}"
                collection = resources.get(resource_name)
                product_count = len(collection.products) if collection else 0
                summary_parts.append(f"  - {resource_name}: {product_count} products")
            
            summary_parts.append(f"  - all_extracted_products: {len(all_products)} products (combined)\n")
            
            # Show sample products
            summary_parts.append("Sample products:")
            for i, product in enumerate(all_products[:5], 1):  # Show first 5
                summary_parts.append(f"{i}. {product.product_name} - {product.price} ({product.store})")
            
            if len(all_products) > 5:
                summary_parts.append(f"... and {len(all_products) - 5} more products")
            
            return "\n".join(summary_parts)
        else:
            message = f"No products found from {len(urls)} URLs"
            streamer.completed(message, {"total_products": 0, "total_urls": len(urls)})
            return f"No products were extracted from the provided URLs"
            
    except Exception as e:
        error_msg = f"Failed to extract products: {str(e)}"
        streamer.error(error_msg)
        return error_msg


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
    Always get images when you need to visually determine if a product matches the user's criteria.

    Parameters:
    - resource_id: The ID of the resource to get
    - limit: Maximum number of products to show (default: 5)
    - max_price: Maximum price filter - only show products under this price (optional)
    - summary: If True, returns just product names; if False, returns full product details (default: True)
    - get_images: If True, returns multimodal content with product images; if False, returns text only (default: False)
    - context_vars: The context variables to use

    Returns list of VisionMultimodalContentItem objects (TextContent and ImageContent) for easy handling in agent.py.
    
    NOTE: Use 'display_items' to stream products to the user for better experience.
    """
)
def get_resource(
    resource_id: str,
    limit: int = 5,
    max_price: float = None,
    summary: bool = True,
    context_vars=None
) -> Union[List[VisionMultimodalContentItem], str]:
    get_images = False

    resources = context_vars.get('resources')
    collection = resources.get(resource_id)
    if not collection:
        # Return as TextContent for consistency
        return [TextContent(text=f"Resource with ID '{resource_id}' not found")]
    
    result = collection.get_products(limit=limit, summary=summary, max_price=max_price)
    
    # If get_images is False, return text-only content
    if not get_images:
        text_result = json.dumps(result, indent=2)
        return [TextContent(text=text_result)]
    
    # If get_images is True, return multimodal content with proper objects
    products = result.get('products', [])
    
    # Create collection info for the helper function
    collection_info = {
        'site_name': collection.site_name or collection.source_name,
        'source_name': collection.source_name
    }
    
    # Use the helper function to create proper content objects
    if not summary and products:  # Only add images for full product data
        return create_multimodal_product_content(products, collection_info)
    else:
        # For summary mode, just return text content
        header_text = f"**{collection.site_name or collection.source_name}** - {len(products)} products found\n\n"
        if summary and products:
            product_names = result.get('products', [])
            if isinstance(product_names, list) and product_names:
                if isinstance(product_names[0], str):
                    # Summary mode returns just names
                    header_text += "Products:\n" + "\n".join(f"• {name}" for name in product_names)
                else:
                    # Fallback if products are still dicts
                    header_text += "Products:\n" + "\n".join(f"• {p.get('product_name', 'Unknown')}" for p in product_names)
        
        return [TextContent(text=header_text)]


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
    description="""
Stream products to the user in real-time with smooth animations.
This is the primary tool for displaying products to create an engaging user experience.
MAKE SURE YOU SHOW THE USER SOME RELEVANT PRODUCTS.

REQUIRED FIELDS for each product dict:
- product_name: Product name/title (string)
- store: Brand or store name (string)
- price: Product price as string (e.g., '$89.99')
- price_value: Product price as float for filtering/sorting
- product_url: URL to the product page (string)
- image_url: Primary product image URL (string)

OPTIONAL FIELDS:
- currency: Price currency (default: "USD")
- sku: Stock Keeping Unit
- product_id: Unique product identifier
- variant_id: Unique variant identifier

Use get_resource(resource_id, summary=false) to get properly formatted product data.
NEVER create fictional product data - always use real scraped data.

Parameters:
- products: List of products to display (Product objects or properly formatted dicts)
- title: Optional title for the product display
"""
)
async def display_items(
    products: List[Union[Product, Dict[str, Any]]],
    title: str = "Products Found",
    context_vars=None
) -> str:
    """Stream products to the user"""
    logger.info(f"🎯 display_items called with {len(products) if products else 0} products")
    
    # Debug logging to catch type issues
    if products:
        first_product_type = type(products[0])
        logger.info(f"🔍 First product type: {first_product_type}")
        if first_product_type is str:
            logger.error(f"❌ BUG: Received string instead of object! First product: {products[0][:100]}")
            return "Error: Products were passed as strings instead of objects. This is a bug in the tool schema."

    try:
        await context_vars.get('agent').stream_products(products=products, title=title)
        return f"Displayed {len(products)} products"
        
    except Exception as e:
        logger.error(f"❌ Error displaying products: {e}", exc_info=True)
        return f"Error displaying products: {str(e)}"
