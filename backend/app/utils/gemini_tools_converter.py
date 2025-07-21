"""
Gemini Tools Converter for Shopping Deals
Adapted from openai_tools_converter.py for shopping functionality
"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel
import asyncio

# Import our new simplified search services
from .hybrid_search_service import shopify_search, hybrid_search
from .google_discovery_service import GoogleDiscoveryService
from .debug_tracker import init_debug_session, get_debug_tracker, finalize_debug_session
from .progress_utils import stream_progress_update, set_streaming_callback
from .funnel_visualizer import init_funnel_tracking, get_funnel_visualizer, finalize_funnel_tracking


@dataclass
class ShoppingContextVariables:
    """Context variables for shopping functions"""
    deals_found: List[Dict[str, Any]] = field(default_factory=list)
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    final_chat_message: str = ""
    total_searches: int = 0
    
    def add_deal(self, deal: Dict[str, Any]):
        """Add a deal to the context"""
        self.deals_found.append(deal)
    
    def add_search_result(self, result: Dict[str, Any]):
        """Add a search result to the context"""
        self.search_results.append(result)


def extract_tool_call_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract tool call information from Gemini response text
    Looks for simple JSON objects with function_name and args
    """
    print(f"DEBUG: Looking for JSON tool calls...")
    
    # Look for JSON objects by finding brackets
    try:
        # Find all JSON-like structures in the response
        i = 0
        while i < len(response_text):
            # Look for opening brace
            start = response_text.find('{', i)
            if start == -1:
                break
                
            # Count braces to find the matching closing brace
            brace_count = 0
            end = start
            
            for j in range(start, len(response_text)):
                if response_text[j] == '{':
                    brace_count += 1
                elif response_text[j] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = j + 1
                        break
            
            if brace_count == 0:  # Found complete JSON object
                json_str = response_text[start:end].strip()
                
                # Check if it looks like a function call
                if '"function_name"' in json_str and '"args"' in json_str:
                    print(f"DEBUG: Found potential JSON: {json_str[:100]}...")
                    
                    try:
                        tool_call = json.loads(json_str)
                        
                        # Validate it has the required keys
                        if "function_name" in tool_call and "args" in tool_call:
                            function_name = tool_call["function_name"]
                            arguments = tool_call["args"]
                            
                            print(f"DEBUG: Successfully parsed tool call: {function_name}")
                            return {
                                "function_name": function_name,
                                "arguments": arguments
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: Failed to parse JSON: {e}")
                        pass
            
            i = start + 1
                    
    except Exception as e:
        print(f"DEBUG: Error in JSON extraction: {e}")
    
    # If no JSON format found, return None
    print(f"DEBUG: No valid JSON tool call found")
    
    return None


async def execute_function_with_context_async(
    function_name: str, 
    arguments: Dict[str, Any], 
    context: ShoppingContextVariables
) -> str:
    """
    Async version of execute_function_with_context
    Execute a function with context variables asynchronously
    """
    try:
        if function_name == "search_product":
            return await search_product(arguments, context)
        elif function_name == "show_products":
            return _show_products(arguments, context)
        elif function_name == "chat_message":
            return _chat_message(arguments, context)
        elif function_name == "show_search_links":
            return _show_search_links(arguments, context)
        else:
            return f"Unknown function: {function_name}"
    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        print(error_msg)
        return error_msg


def search_product_sync(args: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Sync version of search_product for use in sync execution contexts
    """
    import asyncio
    import concurrent.futures
    
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        
        if loop.is_running():
            # If there's already a running loop, use a thread pool to run the async function
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, search_product(args, context))
                return future.result()
        else:
            # No running loop, safe to use run_until_complete
            return loop.run_until_complete(search_product(args, context))
            
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(search_product(args, context))


def execute_function_with_context(
    function_name: str, 
    arguments: Dict[str, Any], 
    context: ShoppingContextVariables
) -> str:
    """
    Execute a function with context variables - sync version
    """
    try:
        if function_name == "search_product":
            return search_product_sync(arguments, context)
        elif function_name == "show_products":
            return _show_products(arguments, context)
        elif function_name == "chat_message":
            return _chat_message(arguments, context)
        elif function_name == "show_search_links":
            return _show_search_links(arguments, context)
        else:
            return f"Unknown function: {function_name}"
    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        print(error_msg)
        return error_msg


# Removed _add_structured_products function - creating duplicates with wrong structure


async def search_product(args: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Enhanced search using our fast Shopify JSON approach
    """
    import time
    
    query = args.get("query", "")
    max_price = args.get("max_price")
    category = args.get("category")
    marketplaces = args.get("marketplaces", ["SHOPIFY"])
    limit = args.get("limit", 50)  # INCREASED default for more domain diversity
    
    print(f"🔍 Searching for: '{query}' (limit: {limit})")
    
    # Initialize debug session for this query
    debug_tracker = init_debug_session(query)
    if debug_tracker:
        debug_tracker.start_timing_phase("total_search")
    
    # Initialize funnel tracking
    funnel_visualizer = init_funnel_tracking(query)
    
    if not query:
        if debug_tracker:
            debug_tracker.track_error("No search query provided", "input_validation")
        return "Error: No search query provided"
    
    try:
        start_time = time.time()
        
        # Create streaming callback to send products to frontend immediately
        def stream_product_callback(product):
            """Stream individual products to frontend as they're found"""
            try:
                # Add product to context immediately
                context.add_deal({
                    'type': 'product',
                    'product_name': product.get('product_name', 'Unknown Product'),
                    'price': product.get('price', 'Price not available'),
                    'price_value': product.get('price_value', 0),
                    'image_url': product.get('image_url', ''),
                    'product_url': product.get('product_url', ''),
                    'store_name': product.get('store_name', 'Unknown Store'),
                    'description': product.get('description', ''),
                    'source': product.get('source', 'shopify_json'),
                    'marketplace': product.get('marketplace', 'SHOPIFY'),
                    'is_available': product.get('is_available', True)
                })
                
                # Stream to frontend via global callback if available
                try:
                    from .progress_utils import get_streaming_callback
                    global_callback = get_streaming_callback()
                    if global_callback:
                        global_callback("product", {
                            'type': 'product',
                            'product_name': product.get('product_name', 'Unknown Product'),
                            'price': product.get('price', 'Price not available'),
                            'price_value': product.get('price_value', 0),
                            'image_url': product.get('image_url', ''),
                            'product_url': product.get('product_url', ''),
                            'store_name': product.get('store_name', 'Unknown Store'),
                            'description': product.get('description', ''),
                            'source': product.get('source', 'shopify_json'),
                            'marketplace': product.get('marketplace', 'SHOPIFY'),
                            'is_available': product.get('is_available', True)
                        })
                except Exception as e:
                    print(f"   ⚠️  Streaming callback error: {e}")
            except Exception as e:
                print(f"   ⚠️  Product callback error: {e}")
        
        # Use our fast Shopify JSON search with streaming
        if "AMAZON" in marketplaces and "SHOPIFY" in marketplaces:
            # Use hybrid search (Shopify + Amazon if available) with streaming
            products = await hybrid_search(query, max_results=limit, product_callback=stream_product_callback)
            search_source = "Shopify stores + Amazon Business"
        else:
            # Use pure Shopify search (fastest) with streaming
            products = await shopify_search(query, max_results=limit, product_callback=stream_product_callback)
            search_source = "Shopify stores"
        
        search_time = time.time() - start_time
        
        if not products:
            return f"No products found for '{query}' in {search_source}"
        
        # Apply price filter if specified
        if max_price:
            print(f"🔍 Filtering {len(products)} products with max_price: ${max_price}")
            filtered_products = []
            for product in products:
                try:
                    price_value = product.get('price_value', 0)
                    price_str = product.get('price', 'No price')
                    product_name = product.get('product_name', 'Unknown')[:30]
                    
                    # Include products if: price_value is 0 (parsing failed) OR price_value <= max_price
                    if price_value == 0 or price_value <= max_price:
                        filtered_products.append(product)
                        print(f"   ✅ Include: {product_name} - {price_str} (value: {price_value})")
                    else:
                        print(f"   ❌ Exclude: {product_name} - {price_str} (value: {price_value}) > ${max_price}")
                except Exception as e:
                    # If price parsing fails, include the product
                    filtered_products.append(product)
                    print(f"   ⚠️  Price error for {product.get('product_name', 'Unknown')[:30]}: {e}")
            
            print(f"🔍 Price filtering: {len(products)} → {len(filtered_products)} products")
            products = filtered_products
        
        # Add products to context
        for product in products:
            context.add_deal({
                'type': 'product',
                'product_name': product.get('product_name', 'Unknown Product'),
                'price': product.get('price', 'Price not available'),
                'price_value': product.get('price_value', 0),
                'image_url': product.get('image_url', ''),
                'product_url': product.get('product_url', ''),
                'store_name': product.get('store_name', 'Unknown Store'),
                'description': product.get('description', ''),
                'source': product.get('source', 'shopify_json'),
                'marketplace': product.get('marketplace', 'SHOPIFY'),
                'is_available': product.get('is_available', True)
            })

        # 🎯 AUTOMATIC PRODUCT DISPLAY - Don't rely on LLM to call show_products!
        if products and len(products) > 0:
            print(f"   🎨 Auto-displaying {len(products)} products to ensure user sees results...")
            
            # Format products for display with enhanced information
            display_products = []
            for i, product in enumerate(products):
                # Add diversity badges based on product characteristics
                badge = ""
                price_val = product.get('price_value', 0)
                store = product.get('store_name', 'Unknown Store')
                
                if i == 0:  # First product gets top pick
                    badge = "🏆 Top Pick"
                elif price_val > 0 and price_val < 50:
                    badge = "💰 Great Value"
                elif price_val > 150:
                    badge = "⭐ Premium Choice"
                elif 'sale' in product.get('product_name', '').lower() or 'discount' in product.get('description', '').lower():
                    badge = "🔥 Sale Price"
                elif len(products) > 5 and i == len(products) - 1:
                    badge = "💎 Hidden Gem"
                
                # Create reasoning based on selection
                reasoning = ""
                if price_val > 0:
                    if price_val < 50:
                        reasoning = f"Excellent value at ${price_val:.0f} from {store}"
                    elif price_val > 150:
                        reasoning = f"Premium quality option from {store}"
                    else:
                        reasoning = f"Well-priced at ${price_val:.0f} from {store}"
                else:
                    reasoning = f"Quality option from {store}"
                
                display_products.append({
                    "name": product.get('product_name', 'Unknown Product'),
                    "price": product.get('price', 'Price not available'),
                    "image_url": product.get('image_url', ''),
                    "product_url": product.get('product_url', ''),
                    "description": product.get('description', ''),
                    "store": product.get('store_name', 'Unknown Store'),
                    "badge": badge,
                    "reasoning": reasoning
                })
            
            # Auto-call show_products to ensure display
            display_args = {
                "products": display_products,
                "title": f"Found {len(products)} Options for '{query}'",
                "subtitle": f"Curated from {search_source}",
                "is_final": True
            }
            
            _show_products(display_args, context)
            print(f"   ✅ Products automatically displayed to user")
        
        context.total_searches += 1
        
        # Create search links for display (using store discovery)
        try:
            if debug_tracker:
                debug_tracker.start_timing_phase("store_discovery")
            discovery = GoogleDiscoveryService()
            stores = discovery.discover_shopify_stores(query, max_results=50)  # INCREASED: More stores for better coverage
            if debug_tracker:
                debug_tracker.end_timing_phase("store_discovery")
                debug_tracker.start_timing_phase("url_validation")
            
            search_links = []
            for store in stores[:12]:  # Still show top 12 links to users (UI limit)
                # Create proper search URLs instead of just store homepages
                search_url = f"https://{store}/search?q={query.replace(' ', '+')}"
                store_homepage = f"https://{store}"
                
                # Validate that the store domain is accessible before adding to links
                if _validate_store_url(store_homepage):
                    search_links.append({
                        'title': f"{store.replace('.myshopify.com', '').replace('-', ' ').title()} Store",
                        'url': search_url,  # Use search URL instead of homepage
                        'description': f"Search for '{query}' at {store.replace('.myshopify.com', '').replace('-', ' ')}",
                        'domain': store,
                        'score': 0.9,
                        'homepage_url': store_homepage  # Keep homepage as fallback
                    })
                else:
                    print(f"   ❌ Skipping inaccessible store: {store}")
            
            if debug_tracker:
                debug_tracker.end_timing_phase("url_validation")
            
            if search_links:
                context.add_deal({
                    'type': 'search_links',
                    'links': search_links,
                    'search_query': query,
                    'total_results': len(search_links)  # Use validated links count
                })
        except Exception as e:
            print(f"Warning: Could not generate search links: {e}")
            if debug_tracker:
                debug_tracker.track_error(str(e), "store_discovery")
        
        # Finalize debug session
        if debug_tracker:
            debug_tracker.end_timing_phase("total_search")
        products_shown = len(products)
        links_shown = len(search_links) if 'search_links' in locals() else 0
        
        # Finalize funnel tracking
        if funnel_visualizer:
            finalize_funnel_tracking()
        
        # Don't finalize yet - wait for LLM selections to be tracked
        
        result_summary = f"Found {len(products)} products from {search_source} in {search_time:.2f}s"
        if max_price:
            result_summary += f" (filtered to under ${max_price})"
        
        return result_summary
        
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        print(error_msg)
        return error_msg


def _validate_store_url(url: str) -> bool:
    """Validate that a store URL is accessible"""
    debug_tracker = get_debug_tracker()
    
    try:
        import requests
        response = requests.head(url, timeout=3)
        is_valid = response.status_code in [200, 301, 302, 403]  # 403 might still be a valid store
        
        if not is_valid and debug_tracker:
            debug_tracker.track_invalid_url(url, f"HTTP {response.status_code}", "domain")
        
        return is_valid
    except Exception as e:
        if debug_tracker:
            debug_tracker.track_validation_error(url, str(e))
        return False  # If we can't reach it, don't include it


def _product_under_price_limit(product: Dict[str, Any], max_price: float) -> bool:
    """Check if a product is under the specified price limit"""
    try:
        price_str = product.get('price', '0')
        # Handle different price formats: "$29.99", "29.99 USD", etc.
        import re
        price_match = re.search(r'[\d,]+\.?\d*', price_str)
        if price_match:
            price_value = float(price_match.group().replace(',', ''))
            return price_value <= max_price
    except (ValueError, AttributeError):
        pass
    return True  # Include product if we can't parse the price


def _plan_search_strategy(query: str, max_price: float = None, category: str = None) -> List[str]:
    """
    STEP 1: Strategic Planning - Generate multiple search strategies
    Like a human shopper would think through different approaches
    """
    strategies = []
    
    # Base strategy: user's exact query
    base_query = query
    if max_price:
        base_query += f" under ${max_price}"
    strategies.append(base_query)
    
    # Strategy 2: Add category context if provided
    if category:
        strategies.append(f"{category} {query}")
    
    # Strategy 3: Look for alternatives and similar items
    if "headphones" in query.lower():
        strategies.extend([
            query.replace("headphones", "earbuds"),
            query + " wireless bluetooth",
            query + " noise canceling"
        ])
    elif "laptop" in query.lower():
        strategies.extend([
            query + " computer notebook",
            query + " ultrabook macbook",
            query + " gaming business"
        ])
    elif "coat" in query.lower() or "jacket" in query.lower():
        strategies.extend([
            query.replace("coat", "jacket"),
            query + " winter outerwear",
            query + " parka puffer"
        ])
    elif "phone" in query.lower():
        strategies.extend([
            query + " smartphone mobile",
            query + " iphone android",
            query + " unlocked carrier"
        ])
    else:
        # Generic alternatives for other products
        strategies.append(f"{query} best rated")
        strategies.append(f"{query} sale discount")
    
    # Strategy 4: Brand-specific searches (if no brand mentioned)
    brands_mentioned = any(brand in query.lower() for brand in 
                          ['apple', 'samsung', 'sony', 'nike', 'adidas', 'amazon', 'google'])
    
    if not brands_mentioned:
        if "headphones" in query.lower():
            strategies.append(f"sony bose headphones {max_price or 'budget'}")
        elif "laptop" in query.lower():
            strategies.append(f"dell hp laptop {max_price or 'affordable'}")
        elif "phone" in query.lower():
            strategies.append(f"iphone samsung phone {max_price or 'budget'}")
    
    # Remove duplicates and limit to 4 strategies for MVP
    unique_strategies = []
    for strategy in strategies:
        if strategy not in unique_strategies:
            unique_strategies.append(strategy)
    
    return unique_strategies[:4]  # Limit to 4 for MVP efficiency


def _compare_prices(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """Placeholder for price comparison functionality"""
    product_name = arguments.get("product_name", "")
    stores = arguments.get("stores", [])
    
    return f"Comparing prices for '{product_name}' across stores: {stores}. This is a placeholder - actual price comparison would be implemented here."


def _add_deal(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """Add a deal to the context"""
    deal_info = arguments.get("deal_info", {})
    
    if deal_info:
        context.deals_found.append(deal_info)
        return f"Added deal: {deal_info.get('product_name', 'Unknown')} at {deal_info.get('price', 'Unknown price')}"
    
    return "No deal information provided"


def _get_user_preferences(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """Get user preferences"""
    return f"User preferences: {context.user_preferences}"


def _update_preferences(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """Update user preferences"""
    new_preferences = arguments.get("preferences", {})
    context.user_preferences.update(new_preferences)
    return f"Updated preferences: {new_preferences}"


def _emit_chat_response(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """Emit a chat response to the user - this is the final step before ending the conversation"""
    message = arguments.get("message", "")
    
    if not message:
        return "Error: No message provided for chat response."
    
    # Validate that we have structured products ready
    structured_products_exist = any(deal.get('type') == 'structured_product' for deal in context.deals_found)
    
    if not structured_products_exist:
        return "Error: Cannot emit chat response - no structured products have been added yet. Call add_structured_products first."
    
    # Mark this message as the final chat response
    context.final_chat_message = message
    
    return f"Chat response ready: '{message}' - Conversation can now end."


# Removed _display_products function - no longer needed to avoid duplicates


def _show_products(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Display curated products - simplified without creating duplicates
    """
    products = arguments.get("products", [])
    title = arguments.get("title", "Products Found")
    subtitle = arguments.get("subtitle", "")
    is_final = arguments.get("is_final", True)
    
    if not products:
        return "No products provided to show"
    
    # Track LLM selection decisions
    debug_tracker = get_debug_tracker()
    
    if debug_tracker and is_final:
        # Extract selection criteria from arguments or infer from products
        criteria = arguments.get("selection_criteria", [
            "Product relevance to query",
            "Price competitiveness", 
            "Store reliability",
            "Product availability"
        ])
        
        # Track the LLM's final product selections
        debug_tracker.track_llm_selection(products, criteria)
        
        # Finalize the debug session now that we have LLM decisions
        debug_tracker.finalize_session(len(products), context.total_searches)
    
    # Instead of creating duplicates, just mark existing products as "curated"
    # and add display metadata to the context for frontend use
    if not hasattr(context, 'display_metadata'):
        context.display_metadata = {}
    
    context.display_metadata.update({
        'title': title,
        'subtitle': subtitle,
        'is_final': is_final,
        'curated_count': len(products)
    })
    
    # Add final flag information
    if is_final:
        result = f"Curated {len(products)} products for display: {title} (Final product selection)"
        # Mark context as having final products
        if not hasattr(context, 'has_final_products'):
            context.has_final_products = True
    else:
        result = f"Curated {len(products)} products for display: {title} (Intermediate product selection)"
    
    return result


def _show_search_links(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Display search result links from Exa to give users something to explore
    This happens early in the search process before full product analysis
    """
    links = arguments.get("links", [])
    search_query = arguments.get("search_query", "")
    total_results = arguments.get("total_results", len(links))
    
    if not links:
        return "No search links provided"
    
    # Create a special search links object that frontend can display
    search_links_data = {
        "type": "search_links",
        "search_query": search_query,
        "total_results": total_results,
        "links": [],
        "timestamp": "now"
    }
    
    # Process and format each link with validation
    valid_links = []
    for link in links:
        if isinstance(link, dict):
            # Link is already structured
            url = link.get("url", "")
            
            # Validate URL format
            if url and _is_valid_url(url):
                formatted_link = {
                    "title": link.get("title", "Unknown Title"),
                    "url": url,
                    "description": link.get("description", ""),
                    "domain": link.get("domain", ""),
                    "score": link.get("score", 0),
                    "highlights": link.get("highlights", [])
                }
                
                # Extract domain from URL if not provided
                if not formatted_link["domain"] and url:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        formatted_link["domain"] = parsed.netloc.replace("www.", "")
                    except:
                        formatted_link["domain"] = "unknown"
                
                valid_links.append(formatted_link)
            else:
                print(f"   ❌ Skipping invalid URL: {url}")
        else:
            # Link is just a URL string
            if _is_valid_url(link):
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(link)
                    domain = parsed.netloc.replace("www.", "")
                    
                    formatted_link = {
                        "title": domain.title().replace('.com', ''),
                        "url": link,
                        "description": f"Visit {domain}",
                        "domain": domain,
                        "score": 0,
                        "highlights": []
                    }
                    valid_links.append(formatted_link)
                except:
                    print(f"   ❌ Error parsing URL: {link}")
            else:
                print(f"   ❌ Skipping invalid URL: {link}")
    
    search_links_data["links"] = valid_links
    search_links_data["total_results"] = len(valid_links)
    
    # Add to context for frontend consumption
    context.deals_found.append(search_links_data)
    
    return f"Displayed {len(valid_links)} valid search links for '{search_query}' (Filtered from {len(links)} total)"


def _is_valid_url(url: str) -> bool:
    """Check if a URL is valid and safe to display"""
    debug_tracker = get_debug_tracker()
    
    if not url or not isinstance(url, str):
        if debug_tracker:
            debug_tracker.track_invalid_url(url, "Empty or invalid URL string", "link")
        return False
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Must have a scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            if debug_tracker:
                debug_tracker.track_invalid_url(url, "Missing scheme or netloc", "link")
            return False
        
        # Only allow http/https
        if parsed.scheme not in ['http', 'https']:
            if debug_tracker:
                debug_tracker.track_invalid_url(url, f"Invalid scheme: {parsed.scheme}", "link")
            return False
        
        # Avoid localhost and internal addresses
        if 'localhost' in parsed.netloc or '127.0.0.1' in parsed.netloc:
            if debug_tracker:
                debug_tracker.track_invalid_url(url, "Localhost or internal address", "link")
            return False
        
        return True
    except Exception as e:
        if debug_tracker:
            debug_tracker.track_validation_error(url, str(e))
        return False


def _chat_message(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Consolidated function for all chat communication
    Handles progress updates, excitement, and final responses
    """
    message = arguments.get("message", "")
    tone = arguments.get("tone", "neutral")  # neutral, excited, celebratory, informative
    includes_reasoning = arguments.get("includes_reasoning", False)
    is_final = arguments.get("is_final", False)
    
    if not message:
        return "No message provided"
    
    # Add tone indicators for frontend display
    tone_prefixes = {
        "excited": "🎉 ",
        "celebratory": "🎊 ", 
        "informative": "ℹ️ ",
        "neutral": ""
    }
    
    formatted_message = tone_prefixes.get(tone, "") + message
    
    # Store message based on type
    if is_final:
        # This is the final chat response
        context.final_chat_message = formatted_message
        return f"Final chat response sent: '{formatted_message}'"
    else:
        # This is a progress update - store in a list for frontend
        if not hasattr(context, 'chat_updates'):
            context.chat_updates = []
        
        context.chat_updates.append({
            "message": formatted_message,
            "tone": tone,
            "timestamp": "now",  # In real app, use actual timestamp
            "includes_reasoning": includes_reasoning
        })
        
        return f"Chat update sent ({tone}): '{formatted_message}'"


def get_structured_products_json(context: ShoppingContextVariables) -> List[Dict[str, Any]]:
    """
    Extract and return ALL data from context for frontend consumption
    This includes products, search links, reasoning, and other UI elements
    """
    all_frontend_data = []
    
    for deal in context.deals_found:
        # Only process regular products and search links - no duplicates
        if deal.get('type') == 'product':
            # Clean structured product for frontend - handle different field name formats
            product_name = deal.get('product_name') or deal.get('name') or 'Unknown Product'
            product_url = deal.get('product_url') or deal.get('url') or ''
            
            # Use store_name first, then store as fallback
            store = deal.get('store_name') or deal.get('store') or 'Unknown Store'
            
            product = {
                "id": f"{product_name}_{hash(product_url)}"[:50],
                "product_name": product_name,
                "name": product_name,
                "price": deal.get('price', 'Price not available'),
                "store": store,
                "image_url": deal.get('image_url', ''),
                "product_url": product_url,
                "description": deal.get('description', ''),
                "category": deal.get('category', ''),
                "availability": deal.get('availability', 'In Stock'),
                "rating": deal.get('rating', 'N/A'),
                "badge": deal.get('badge', ''),
                "reasoning": deal.get('reasoning', ''),
                "type": "product",  # Normalized type for frontend
                "price_value": deal.get('price_value', 0),  # Include price value for sorting
                "source": deal.get('source', 'shopify_json')
            }
            all_frontend_data.append(product)
            
        elif deal.get('type') == 'search_links':
            # Search links data - pass through as-is with normalized type
            search_links = deal.copy()
            search_links['type'] = 'search_links'
            # Ensure it has an ID for frontend
            if not search_links.get('id'):
                search_links['id'] = f"search-{hash(str(search_links))}"[:20]
            all_frontend_data.append(search_links)
            
        elif deal.get('type') == 'reasoning' or (deal.get('reasoning_type') and deal.get('title')):
            # Reasoning data - pass through as-is with normalized type
            reasoning = deal.copy()
            reasoning['type'] = 'reasoning'
            # Ensure it has an ID for frontend
            if not reasoning.get('id'):
                reasoning['id'] = f"reasoning-{hash(str(reasoning))}"[:20]
            all_frontend_data.append(reasoning)
        
        # Skip display_product and structured_product types to avoid duplicates
    
    # Add display metadata if available
    if hasattr(context, 'display_metadata'):
        display_meta = {
            "type": "display_metadata",
            "id": "display_meta",
            **context.display_metadata
        }
        all_frontend_data.append(display_meta)
    
    return all_frontend_data 