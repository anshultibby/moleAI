"""Tool registry for collecting and organizing all available tools"""

from typing import List
from .base import Tool
from .decorator import create_tool
from .search_tools import discover_stores, fetch_products
from .product_tools import add_product
from ..utils.debug_logger import debug_log


def get_tools() -> List[Tool]:
    """Get all tools for the agent"""
    debug_log("Creating tools...")
    
    tools = [
        create_tool(discover_stores),
        create_tool(fetch_products),
        create_tool(add_product)
    ]
    
    debug_log(f"Created {len(tools)} tools")
    return tools
 