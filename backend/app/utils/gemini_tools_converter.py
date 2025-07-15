"""
Gemini Tools Converter for Shopping Deals
Adapted from openai_tools_converter.py for shopping functionality
"""

import json
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from pydantic import BaseModel


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
    """Placeholder for product search functionality"""
    query = arguments.get("query", "")
    max_price = arguments.get("max_price", None)
    category = arguments.get("category", None)
    
    # Add to search history
    context.search_history.append(query)
    
    # Placeholder response
    return f"Searching for '{query}' with max price {max_price} in category {category}. This is a placeholder - actual product search would be implemented here."


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