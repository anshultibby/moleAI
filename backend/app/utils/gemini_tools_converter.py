"""
Gemini Tools Converter for Shopping Deals
Adapted from openai_tools_converter.py for shopping functionality
"""

import json
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from pydantic import BaseModel
from .firecrawl_service import FirecrawlService
import os


@dataclass
class ShoppingContextVariables:
    """Context variables for shopping deals processing"""
    deals_found: List[Dict[str, Any]]
    search_history: List[str]
    user_preferences: Dict[str, Any]
    
    def __init__(self):
        self.deals_found = []
        self.search_history = []
        self.user_preferences = {}


def extract_tool_call_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract tool call information from Gemini response text
    Looks for function calls in the format: function_name(arguments)
    """
    # Pattern to match function calls like: search_product({"query": "laptop", "max_price": 1000})
    pattern = r'(\w+)\s*\(\s*({.*?})\s*\)'
    
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        function_name = match.group(1)
        try:
            arguments = json.loads(match.group(2))
            return {
                "function_name": function_name,
                "arguments": arguments
            }
        except json.JSONDecodeError:
            return None
    
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
    elif function_name == "compare_prices":
        return _compare_prices(arguments, context)
    elif function_name == "add_deal":
        return _add_deal(arguments, context)
    elif function_name == "get_user_preferences":
        return _get_user_preferences(arguments, context)
    elif function_name == "update_preferences":
        return _update_preferences(arguments, context)
    else:
        return f"Unknown function: {function_name}"


def _search_product(arguments: Dict[str, Any], context: ShoppingContextVariables) -> str:
    """Search for products using Firecrawl service"""
    query = arguments.get("query", "")
    max_price = arguments.get("max_price", None)
    category = arguments.get("category", None)
    
    # Add to search history
    context.search_history.append(query)
    
    try:
        # Initialize Firecrawl service
        firecrawl_service = FirecrawlService()
        
        # Search for products (now returns full content from Zara)
        search_results = firecrawl_service.search_products(query, max_price, category)
        
        if search_results:
            # Add the raw content to context for LLM processing
            for result in search_results:
                context.deals_found.append(result)
            
            # Return the full content for the LLM to process
            result_text = f"Found search results for '{query}' from Zara:\n\n"
            
            for result in search_results:
                result_text += f"Source: {result.get('source', 'Unknown')}\n"
                result_text += f"Search URL: {result.get('url', 'N/A')}\n"
                result_text += f"Page Title: {result.get('metadata', {}).get('title', 'N/A')}\n\n"
                
                # Include the full markdown content for LLM processing
                markdown_content = result.get('markdown', '')
                if markdown_content:
                    result_text += "Page Content:\n"
                    result_text += markdown_content
                    result_text += "\n\n"
                else:
                    result_text += "No content available\n\n"
            
            result_text += f"Please analyze this content and extract relevant product information including names, prices, and availability."
            
            return result_text
        else:
            return f"No search results found for '{query}' on Zara. Try a different search term or check if the Firecrawl API is properly configured."
            
    except ValueError as e:
        if "Firecrawl API key not configured" in str(e):
            return "Firecrawl API key not configured. Please set FIRECRAWL_API_KEY environment variable."
        else:
            return f"Error searching for products: {str(e)}"
    except Exception as e:
        return f"Error searching for products: {str(e)}"


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