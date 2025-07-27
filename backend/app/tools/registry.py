"""Tool registry for collecting and organizing all available tools"""

from typing import List
from .base import Tool
from .decorator import create_tool
from .search_tools import discover_stores, fetch_products
from .product_tools import display_product, get_displayed_products, remove_displayed_products
from ..utils.debug_logger import debug_log


def get_tools() -> List[Tool]:
    """Get all tools for the agent"""
    debug_log("Creating tools...")
    
    tools = [
        create_tool(discover_stores),
        create_tool(fetch_products),
        create_tool(display_product),
        create_tool(get_displayed_products),
        create_tool(remove_displayed_products)
    ]
    
    debug_log(f"Created {len(tools)} tools")
    return tools
 