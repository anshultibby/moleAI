"""Tool function definitions - Define your functions here to convert them to tools"""

from typing import Optional, List
from app.tools import tool


# Example tool function - you can replace this with your own functions
@tool(
    name="search_google_shopping",
    description="Looks up products on Google Shopping."
)
def search_google_shopping(query: str) -> str:
    """Looks up products on Google Shopping."""
    # Your implementation here
    return f"Products on Google Shopping for {query}"
