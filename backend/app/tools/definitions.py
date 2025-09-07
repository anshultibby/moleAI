"""Tool function definitions - Define your functions here to convert them to tools"""

from typing import Optional, List, Dict, Any
from app.tools import tool
from app.modules.serp import search_jina, SearchError


@tool(
    name="search_web_with_content",
    description="Search the web using Jina AI and return results with full page content in markdown format."
)
def search_web_with_content(
    query: str,
    num_results: Optional[int] = 5,
    provider: Optional[str] = "google"
) -> Dict[str, Any]:
    """
    Search the web and get full content of result pages using Jina AI.
    
    Args:
        query: The search query string
        num_results: Number of results to return (1-20, default: 5)
        provider: Search provider - "google", "bing", or "reader" (default: "google")
    
    Returns:
        Dictionary containing search results with full page content, links, and images
    """
    try:
        if not query or not query.strip():
            return {"error": "Query cannot be empty"}
        
        if num_results < 1 or num_results > 20:
            return {"error": "num_results must be between 1 and 20"}
        
        # Use the comprehensive search function that reads full content
        results = search_jina(
            query=query.strip(),
            num_results=num_results,
            provider=provider,
            read_content=True,
            respond_with="markdown",
            with_links_summary=True,
            with_images_summary=True,
            with_generated_alt=True
        )
        
        return results
        
    except SearchError as e:
        return {"error": f"Search error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}}
