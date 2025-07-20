"""
Gemini Tools Converter for Shopping Deals
Adapted from openai_tools_converter.py for shopping functionality
"""

import json
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from pydantic import BaseModel
from .hybrid_search_service import search_products_hybrid
import os


@dataclass
class ShoppingContextVariables:
    """Context variables for shopping deals processing"""
    deals_found: List[Dict[str, Any]]
    search_history: List[str]
    user_preferences: Dict[str, Any]
    final_chat_message: str
    
    def __init__(self):
        self.deals_found = []
        self.search_history = []
        self.user_preferences = {}
        self.final_chat_message = ""


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


def execute_function_with_context(
    function_name: str, 
    arguments: Dict[str, Any], 
    context: ShoppingContextVariables
) -> str:
    """
    Execute a function call with the given context
    This is where actual tool implementations would go
    """
    
    if function_name == "search_product":
        return _search_product(arguments, context)
    elif function_name == "show_products":
        return _show_products(arguments, context)
    elif function_name == "chat_message":
        return _chat_message(arguments, context)
    elif function_name == "display_products":
        return _display_products(arguments, context)
    elif function_name == "show_products":
        return _show_products(arguments, context)
    elif function_name == "share_reasoning":
        return _share_reasoning(arguments, context)
    elif function_name == "chat_message":
        return _chat_message(arguments, context)
    elif function_name == "compare_prices":
        return _compare_prices(arguments, context)
    elif function_name == "add_deal":
        return _add_deal(arguments, context)
    elif function_name == "get_user_preferences":
        return _get_user_preferences(arguments, context)
    elif function_name == "update_preferences":
        return _update_preferences(arguments, context)
    elif function_name == "show_search_links":
        return _show_search_links(arguments, context)
    else:
        return f"Unknown function: {function_name}"


def _add_structured_products(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """Add structured product data for frontend display"""
    products = arguments.get("products", [])
    
    if not products:
        return "No products provided"
    
    # Clear existing deals and add structured products
    context.deals_found = []
    
    for product in products:
        # Enhanced image URL processing for multiple stores
        image_url = product.get("image_url", "")
        store_name = product.get("store", "Unknown Store")
        
        if image_url:
            # Handle different URL formats for different stores
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            elif image_url.startswith("/"):
                # Determine the correct domain based on store
                if "zara" in store_name.lower():
                    image_url = "https://www.zara.com" + image_url
                elif "h&m" in store_name.lower() or "hm" in store_name.lower():
                    image_url = "https://www2.hm.com" + image_url
                elif "uniqlo" in store_name.lower():
                    image_url = "https://www.uniqlo.com" + image_url
                elif "forever" in store_name.lower():
                    image_url = "https://www.forever21.com" + image_url
                elif "asos" in store_name.lower():
                    image_url = "https://www.asos.com" + image_url
                else:
                    # Default fallback - try to infer from product_url if available
                    product_url = product.get("product_url", "")
                    if product_url:
                        try:
                            from urllib.parse import urlparse
                            parsed = urlparse(product_url)
                            domain = parsed.netloc
                            image_url = f"https://{domain}" + image_url
                        except:
                            image_url = "https://example.com" + image_url  # Fallback
            elif not image_url.startswith("http"):
                # Handle relative URLs without leading slash
                if "zara" in store_name.lower():
                    image_url = "https://www.zara.com/" + image_url.lstrip("/")
                elif "h&m" in store_name.lower() or "hm" in store_name.lower():
                    image_url = "https://www2.hm.com/" + image_url.lstrip("/")
                elif "uniqlo" in store_name.lower():
                    image_url = "https://www.uniqlo.com/" + image_url.lstrip("/")
                elif "forever" in store_name.lower():
                    image_url = "https://www.forever21.com/" + image_url.lstrip("/")
                elif "asos" in store_name.lower():
                    image_url = "https://www.asos.com/" + image_url.lstrip("/")
            
            # Add quality parameters for specific stores if not present
            if "zara" in store_name.lower() and "w=" not in image_url and "width=" not in image_url:
                separator = "&" if "?" in image_url else "?"
                image_url += f"{separator}w=400&h=500&f=auto&q=85"
        
        # Enhanced product name processing
        product_name = product.get("name", "Unknown Product")
        if not product_name or product_name.lower() in ["unknown product", "product", "item"]:
            # Try to create a better name from description or use fallback
            description = product.get("description", "")
            if description:
                # Take first meaningful words from description
                words = description.split()[:3]
                product_name = " ".join(words).title()
            else:
                product_name = "Fashion Item"
        
        # Clean up the product name
        product_name = product_name.strip().title()
        
        structured_product = {
            "product_name": product_name,
            "price": product.get("price", "Price not available"),
            "store": store_name,
            "image_url": image_url,
            "product_url": product.get("product_url", ""),
            "description": product.get("description", ""),
            "type": "structured_product"  # Flag to identify structured products
        }
        context.deals_found.append(structured_product)
    
    return f"Added {len(products)} structured products for display"


def _search_product(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Rye API Product Search:
    Uses Rye's GraphQL API to search for products from Amazon and Shopify
    """
    import time
    search_start = time.time()
    
    query = arguments.get("query", "")
    max_price = arguments.get("max_price", None)
    category = arguments.get("category", None)
    marketplaces = arguments.get("marketplaces", ["AMAZON", "SHOPIFY"])
    limit = arguments.get("limit", 20)  # Increased for better variety
    
    # Add to search history
    context.search_history.append(query)
    
    try:
        print(f"🛍️ Starting Rye API search for: '{query}'")
        print(f"🕐 TIMING: Search started at {time.strftime('%H:%M:%S')}")
        
        # Import Rye service
        from .rye_service import search_products_with_rye, search_products_by_domain_with_rye
        
        # Get RYE API key from environment
        import os
        rye_api_key = os.getenv("RYE_API_KEY")
        rye_shopper_ip = os.getenv("RYE_SHOPPER_IP", "127.0.0.1")
        
        if not rye_api_key:
            return "❌ RYE_API_KEY not configured. Please set the RYE_API_KEY environment variable."
        
        print("Step 1: Searching Rye API for products...")
        
        # Search using Rye API
        api_start = time.time()
        products = search_products_with_rye(
            query=query,
            api_key=rye_api_key,
            shopper_ip=rye_shopper_ip,
            limit=limit,
            marketplaces=marketplaces
        )
        api_end = time.time()
        print(f"🕐 TIMING: Rye API search took {api_end - api_start:.2f}s")
        
        if not products:
            # Try searching popular domains if direct search didn't work
            print("Step 2: Trying domain-specific searches...")
            popular_domains = ["amazon.com", "shop.gymshark.com", "us.allbirds.com"]
            
            for domain in popular_domains:
                domain_products = search_products_by_domain_with_rye(
                    domain=domain,
                    api_key=rye_api_key,
                    shopper_ip=rye_shopper_ip,
                    limit=5
                )
                # Filter products that match our query
                filtered_products = [
                    p for p in domain_products 
                    if query.lower() in p.get('product_name', '').lower() or 
                       query.lower() in p.get('description', '').lower()
                ]
                products.extend(filtered_products)
                
                if len(products) >= 10:  # Stop if we have enough products
                    break
        
        if not products:
            return f"No products found for '{query}' using Rye API. The query might be too specific or the products might not be available in Rye's catalog."
        
        print(f"Found {len(products)} products via Rye API")
        
        # Add products to context for LLM processing
        for product in products:
            # Apply price filter if specified
            if max_price:
                try:
                    # Extract numeric price from price string
                    price_str = product.get('price', '0')
                    price_value = float(''.join(filter(str.isdigit, price_str.split()[0])))
                    if price_value > max_price:
                        continue
                except (ValueError, IndexError):
                    # If we can't parse the price, include the product
                    pass
            
            # Enhance product data with Rye-specific information
            enhanced_product = {
                **product,
                "source": "rye_api",
                "search_query": query,
                "timestamp": time.strftime('%H:%M:%S')
            }
            context.deals_found.append(enhanced_product)
        
        # Filter products in context by price if specified
        if max_price:
            original_count = len(context.deals_found)
            context.deals_found = [
                deal for deal in context.deals_found 
                if _product_under_price_limit(deal, max_price)
            ]
            filtered_count = len(context.deals_found)
            if filtered_count < original_count:
                print(f"Filtered {original_count - filtered_count} products over ${max_price}")
        
        # Create result summary
        search_end = time.time()
        total_time = search_end - search_start
        
        result_summary = f"🎯 RYE API SEARCH RESULTS for '{query}'\n"
        result_summary += f"Found {len(products)} products in {total_time:.2f}s\n\n"
        
        # Group by marketplace
        amazon_products = [p for p in products if p.get('marketplace') == 'AMAZON']
        shopify_products = [p for p in products if p.get('marketplace') == 'SHOPIFY']
        
        if amazon_products:
            result_summary += f"AMAZON PRODUCTS ({len(amazon_products)}):\n"
            for i, product in enumerate(amazon_products[:3], 1):
                result_summary += f"  {i}. {product.get('product_name', 'N/A')} - {product.get('price', 'N/A')}\n"
        
        if shopify_products:
            result_summary += f"\nSHOPIFY PRODUCTS ({len(shopify_products)}):\n"
            for i, product in enumerate(shopify_products[:3], 1):
                result_summary += f"  {i}. {product.get('product_name', 'N/A')} - {product.get('price', 'N/A')}\n"
        
        result_summary += f"\n✅ All products loaded into context for AI analysis and curation."
        result_summary += f"\n🛒 Products are ready for purchase through Rye's integrated checkout system."
        
        if max_price:
            result_summary += f"\n💰 Price filter: Under ${max_price}"
        
        print(f"🕐 TIMING: Total search time: {total_time:.2f}s")
        
        return result_summary
        
    except Exception as e:
        error_msg = f"Error in Rye API search: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


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


def _display_products(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Display curated products in the frontend visual panel
    Separate from chat - this is for the product cards/grid view
    """
    products = arguments.get("products", [])
    display_title = arguments.get("title", "Products Found")
    display_subtitle = arguments.get("subtitle", "")
    
    if not products:
        return "No products provided for display"
    
    # Don't clear existing deals - we want to keep reasoning and search links
    # Just add the new structured products
    
    for product in products:
        # Enhanced product structure for frontend display
        display_product = {
            "product_name": product.get("name", "Unknown Product"),
            "price": product.get("price", "Price not available"),
            "store": product.get("store", "Unknown Store"),
            "image_url": product.get("image_url", ""),
            "product_url": product.get("product_url", ""),
            "description": product.get("description", ""),
            "type": "display_product",  # Flag for frontend
            "display_title": display_title,
            "display_subtitle": display_subtitle,
            
            # Additional display metadata
            "reasoning": product.get("reasoning", ""),  # Why this product was selected
            "highlights": product.get("highlights", []),  # Key features
            "badge": product.get("badge", ""),  # "Best Value", "Premium Choice", etc.
            "availability": product.get("availability", "unknown"),
            "rating": product.get("rating", ""),
            "brand": product.get("brand", ""),
            
            # Display formatting
            "display_order": product.get("display_order", len(context.deals_found) + 1),
            "category": product.get("category", ""),
        }
        
        # Handle image URL processing for different stores
        image_url = display_product["image_url"]
        store_name = display_product["store"]
        
        if image_url and not image_url.startswith("http"):
            # Convert relative URLs to absolute
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            elif image_url.startswith("/"):
                # Store-specific domain mapping
                store_domains = {
                    "amazon": "https://www.amazon.com",
                    "target": "https://www.target.com",
                    "walmart": "https://www.walmart.com",
                    "best buy": "https://www.bestbuy.com",
                }
                
                for store_key, domain in store_domains.items():
                    if store_key in store_name.lower():
                        image_url = domain + image_url
                        break
                        
            display_product["image_url"] = image_url
        
        context.deals_found.append(display_product)
    
    return f"Displayed {len(products)} products in frontend panel: {display_title}"


def _share_reasoning(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Share reasoning chain with user in the chat interface
    This explains the thinking process and analysis
    """
    reasoning_type = arguments.get("type", "analysis")  # "analysis", "comparison", "recommendation"
    title = arguments.get("title", "My Analysis")
    steps = arguments.get("steps", [])
    conclusion = arguments.get("conclusion", "")
    confidence = arguments.get("confidence", "high")  # "high", "medium", "low"
    
    if not steps and not conclusion:
        return "No reasoning provided to share"
    
    # Build simplified reasoning text for chat display
    type_icon = {"analysis": "🔍", "comparison": "⚖️", "recommendation": "💡"}.get(reasoning_type, "💭")
    
    reasoning_text = f"""
<div class="reasoning-content">
    <div class="reasoning-header">
        <span class="reasoning-icon">{type_icon}</span>
        <strong>{title}</strong>
    </div>
"""
    
    # Add step-by-step reasoning
    if steps:
        for i, step in enumerate(steps, 1):
            step_text = step.get("text", "") if isinstance(step, dict) else str(step)
            reasoning_text += f"""
    <div class="reasoning-step">
        <strong>Step {i}:</strong> {step_text}
    </div>"""
    
    # Add conclusion
    if conclusion:
        reasoning_text += f"""
    <div class="reasoning-conclusion">
        <strong>🎯 Conclusion:</strong> {conclusion}
    </div>"""
    
    # Add confidence indicator
    confidence_icons = {"high": "🟢", "medium": "🟡", "low": "🟠"}
    confidence_icon = confidence_icons.get(confidence, "🟢")
    
    reasoning_text += f"""
    <div class="reasoning-confidence">
        {confidence_icon} <strong>Confidence:</strong> {confidence.title()}
    </div>
</div>"""
    
    # Store reasoning in context for potential display
    if not hasattr(context, 'reasoning_chains'):
        context.reasoning_chains = []
    
    reasoning_data = {
        "type": "reasoning",
        "reasoning_type": reasoning_type,
        "title": title,
        "steps": steps,
        "conclusion": conclusion,
        "confidence": confidence,
        "formatted_text": reasoning_text,
        "timestamp": "now",  # In real app, you'd use actual timestamp
        "id": f"reasoning-{len(context.reasoning_chains)}-{hash(title)}"[:20]
    }
    
    context.reasoning_chains.append(reasoning_data)
    
    # CRITICAL: Add reasoning to deals_found so it gets sent to frontend
    context.deals_found.append(reasoning_data)
    
    # Add reasoning to final chat message for immediate display
    if context.final_chat_message:
        context.final_chat_message += f"\n\n{reasoning_text}"
    else:
        context.final_chat_message = reasoning_text
    
    return f"Shared {reasoning_type} reasoning with {len(steps)} steps"


def _show_products(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """
    Consolidated function that combines display_products functionality
    Enhanced with is_final flag for better flow control
    """
    products = arguments.get("products", [])
    title = arguments.get("title", "Products Found")
    subtitle = arguments.get("subtitle", "")
    is_final = arguments.get("is_final", True)
    
    if not products:
        return "No products provided to show"
    
    # Use the existing display_products logic
    result = _display_products({
        "products": products,
        "title": title,
        "subtitle": subtitle
    }, context)
    
    # Add final flag information
    if is_final:
        result += " (Final product selection)"
        # Mark context as having final products
        if not hasattr(context, 'has_final_products'):
            context.has_final_products = True
    else:
        result += " (Intermediate product selection)"
    
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
    
    # Process and format each link
    for link in links:
        if isinstance(link, dict):
            # Link is already structured
            formatted_link = {
                "title": link.get("title", "Unknown Title"),
                "url": link.get("url", ""),
                "description": link.get("description", ""),
                "domain": link.get("domain", ""),
                "score": link.get("score", 0),
                "highlights": link.get("highlights", [])
            }
        else:
            # Link is just a URL string
            formatted_link = {
                "title": link,
                "url": link,
                "description": "",
                "domain": "",
                "score": 0,
                "highlights": []
            }
        
        # Extract domain from URL if not provided
        if not formatted_link["domain"] and formatted_link["url"]:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(formatted_link["url"])
                formatted_link["domain"] = parsed.netloc.replace("www.", "")
            except:
                formatted_link["domain"] = "unknown"
        
        search_links_data["links"].append(formatted_link)
    
    # Add to context for frontend consumption
    context.deals_found.append(search_links_data)
    
    return f"Displayed {len(links)} search links for '{search_query}' (Total: {total_results} results found)"


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
        # Handle different types of data
        if deal.get('type') in ['structured_product', 'display_product', 'product']:
            # Clean structured product for frontend - handle different field name formats
            product_name = deal.get('product_name') or deal.get('name') or 'Unknown Product'
            product_url = deal.get('product_url') or deal.get('url') or ''
            
            product = {
                "id": f"{product_name}_{hash(product_url)}"[:50],
                "product_name": product_name,
                "name": product_name,
                "price": deal.get('price', 'Price not available'),
                "store": deal.get('store', 'Unknown Store'),
                "image_url": deal.get('image_url', ''),
                "product_url": product_url,
                "description": deal.get('description', ''),
                "category": deal.get('category', ''),
                "availability": deal.get('availability', 'In Stock'),
                "rating": deal.get('rating', 'N/A'),
                "badge": deal.get('badge', ''),
                "reasoning": deal.get('reasoning', ''),
                "type": "product"  # Normalized type for frontend
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
            
        else:
            # Handle legacy product data without proper type
            if deal.get('store_name') or deal.get('product_name') or deal.get('name'):
                # This looks like a product, convert it
                product = {
                    "id": f"{deal.get('product_name', deal.get('name', 'unknown'))}_{hash(deal.get('url', ''))}"[:50],
                    "product_name": deal.get('product_name') or deal.get('name') or 'Unknown Product',
                    "name": deal.get('product_name') or deal.get('name') or 'Unknown Product',
                    "price": deal.get('price', 'Price not available'),
                    "store": deal.get('store_name') or deal.get('store') or 'Unknown Store',
                    "image_url": deal.get('image_url', ''),
                    "product_url": deal.get('url') or deal.get('product_url', ''),
                    "description": deal.get('description', ''),
                    "category": deal.get('category', ''),
                    "availability": "In Stock",
                    "rating": "N/A",
                    "type": "product"  # Normalized type for frontend
                }
                all_frontend_data.append(product)
    
    return all_frontend_data 