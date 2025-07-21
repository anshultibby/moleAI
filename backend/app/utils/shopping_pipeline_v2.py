"""
Simplified Shopping Pipeline using Standard OpenAI Chat Completion Pattern
"""

import json
import time
from typing import List, Dict, Any, Tuple, Generator
import openai
from dataclasses import dataclass

@dataclass
class ShoppingContext:
    """Simple context for maintaining state across function calls"""
    deals_found: List[Dict[str, Any]] = None
    final_message: str = ""
    
    def __post_init__(self):
        if self.deals_found is None:
            self.deals_found = []

def create_tools():
    """Define the available tools/functions for the AI"""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_product",
                "description": "Search for products across online marketplaces",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for products (e.g., 'black dress', 'wireless headphones')"
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price limit for products"
                        },
                        "marketplaces": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of marketplaces to search (e.g., ['SHOPIFY', 'AMAZON'])"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of products to return (default 20)"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "show_products",
                "description": "Display curated products to the user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "products": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "price": {"type": "string"},
                                    "image_url": {"type": "string"},
                                    "product_url": {"type": "string"},
                                    "description": {"type": "string"},
                                    "store": {"type": "string"},
                                    "badge": {"type": "string"},
                                    "reasoning": {"type": "string"}
                                }
                            }
                        },
                        "title": {"type": "string"},
                        "subtitle": {"type": "string"},
                        "is_final": {"type": "boolean"}
                    },
                    "required": ["products", "title"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "chat_message",
                "description": "Send a final message to complete the conversation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "is_final": {"type": "boolean"}
                    },
                    "required": ["message", "is_final"]
                }
            }
        }
    ]

def execute_function(function_name: str, arguments: Dict[str, Any], context: ShoppingContext) -> str:
    """Execute a function call and return the result"""
    if function_name == "search_product":
        # Import here to avoid circular imports
        from .hybrid_search_service import HybridSearchService
        import asyncio
        
        query = arguments.get("query", "")
        max_price = arguments.get("max_price")
        marketplaces = arguments.get("marketplaces", ["SHOPIFY"])
        limit = arguments.get("limit", 20)
        
        print(f"🔍 Searching for: '{query}' (limit: {limit})")
        
        try:
            hybrid = HybridSearchService()
            
            async def run_search():
                include_amazon = "AMAZON" in marketplaces
                return await hybrid.search(query, max_results=limit, include_amazon=include_amazon)
            
            result = asyncio.run(run_search())
            
            # Store products in context
            context.deals_found = result.products
            
            # Apply price filtering if specified
            if max_price:
                filtered_products = []
                for product in result.products:
                    try:
                        price_value = float(product.get('price_value', 0))
                        if price_value <= max_price:
                            filtered_products.append(product)
                    except (ValueError, TypeError):
                        continue
                
                print(f"🔍 Price filtering: {len(result.products)} → {len(filtered_products)} products")
                context.deals_found = filtered_products
                
                return f"Found {len(filtered_products)} products from {marketplaces[0]} stores in {result.search_time:.1f}s (filtered to under ${max_price})"
            
            return f"Found {len(result.products)} products from {marketplaces[0]} stores in {result.search_time:.1f}s"
            
        except Exception as e:
            return f"Search failed: {str(e)}"
    
    elif function_name == "show_products":
        products = arguments.get("products", [])
        title = arguments.get("title", "Products")
        subtitle = arguments.get("subtitle", "")
        is_final = arguments.get("is_final", False)
        
        # This would normally send to frontend - for now just return success
        return f"Displayed {len(products)} products in frontend panel: {title}" + (" (Final product selection)" if is_final else "")
    
    elif function_name == "chat_message":
        message = arguments.get("message", "")
        is_final = arguments.get("is_final", False)
        
        if is_final:
            context.final_message = message
            return f"Final chat response sent: '{message}'"
        else:
            return f"Chat message sent: '{message}'"
    
    else:
        return f"Unknown function: {function_name}"

def get_system_prompt():
    """Get the system prompt for the shopping assistant"""
    return """You are an expert shopping assistant that helps users find products online. Your goal is to:

1. **Search for products** using search_product when users ask for items
2. **Display results** using show_products to show curated product selections  
3. **Complete conversations** using chat_message with is_final=true

**Important guidelines:**
- When you find few results (1-3 products), consider expanding your search with broader terms or higher price limits
- Always display products using show_products after successful searches
- End conversations with chat_message and is_final=true
- Be helpful and conversational in your responses

Start by understanding what the user wants, then search for relevant products."""

def trim_conversation_history(messages: List[Dict[str, Any]], max_messages: int = 10) -> List[Dict[str, Any]]:
    """
    Keep conversation history manageable by preserving only recent messages
    Always keeps system prompt and first user message, then keeps the most recent messages
    """
    if len(messages) <= max_messages:
        return messages
    
    # Always preserve system and initial user message
    preserved = messages[:2]  # system + user
    
    # Keep the most recent messages (max_messages - 2 to account for preserved messages)
    recent_messages = messages[-(max_messages - 2):]
    
    trimmed = preserved + recent_messages
    
    print(f"📝 Trimmed conversation: {len(messages)} → {len(trimmed)} messages")
    return trimmed

def process_shopping_query_simple(user_query: str, api_key: str, max_iterations: int = 10) -> Generator[Dict[str, Any], None, None]:
    """
    Process shopping query using standard OpenAI conversation pattern
    
    Yields:
        Dict with 'type' and relevant data for each step
    """
    print(f"🛍️ Processing query: '{user_query}'")
    
    # Initialize conversation
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": user_query}
    ]
    
    context = ShoppingContext()
    client = openai.OpenAI(api_key=api_key)
    tools = create_tools()
    
    for iteration in range(max_iterations):
        try:
            print(f"🔄 Iteration {iteration + 1}/{max_iterations}")
            
            # Trim conversation history to keep it manageable
            messages = trim_conversation_history(messages, max_messages=10)
            
            # Get AI response
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1
            )
            
            message = response.choices[0].message
            
            # Add assistant message to conversation
            messages.append({
                "role": "assistant", 
                "content": message.content,
                "tool_calls": message.tool_calls
            })
            
            # Handle tool calls
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    print(f"🔧 Executing: {function_name} with {arguments}")
                    
                    # Execute function
                    result = execute_function(function_name, arguments, context)
                    
                    # Add tool result to conversation  
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                    
                    # Yield progress update
                    yield {
                        "type": "function_result",
                        "function": function_name,
                        "result": result
                    }
                    
                    # Check for completion
                    if function_name == "chat_message" and arguments.get("is_final"):
                        yield {
                            "type": "final_response", 
                            "message": context.final_message,
                            "products": context.deals_found
                        }
                        return
            
            # Handle regular text response (no function calls)
            elif message.content:
                yield {
                    "type": "assistant_message",
                    "content": message.content
                }
                
                # If no tool calls and we have products, suggest next steps
                if context.deals_found and not any("show_products" in str(msg) for msg in messages[-5:]):
                    messages.append({
                        "role": "user",
                        "content": "You have search results. Please use show_products to display them to the user, then complete with chat_message."
                    })
            
        except Exception as e:
            print(f"❌ Error in iteration {iteration + 1}: {e}")
            yield {
                "type": "error",
                "message": str(e)
            }
            break
    
    # If we exit the loop without completion
    if not context.final_message:
        yield {
            "type": "final_response",
            "message": "I found some great options for you!",
            "products": context.deals_found
        }

# Export the main function
__all__ = ["process_shopping_query_simple"] 