"""Search module using Jina AI Search API (s.jina.ai)"""

import os
import requests
from typing import Dict, Any, Optional
from loguru import logger


class SearchError(Exception):
    """Custom exception for search-related errors"""
    pass


class JinaSearchClient:
    """Client for interacting with Jina AI Search API (s.jina.ai)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Jina Search client
        
        Args:
            api_key: Jina AI API key. If None, will try to get from JINA_AI_API_KEY env var
        """
        self.api_key = api_key or os.getenv("JINA_AI_API_KEY")
        if not self.api_key:
            raise SearchError("JINA_AI_API_KEY not provided and not found in environment variables")
        
        self.base_url = "https://s.jina.ai"
        self.timeout = 30
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        provider: str = "google",
        country: str = "us",
        language: str = "en",
        read_content: bool = False,
        with_links_summary: bool = True,
        with_images_summary: bool = True,
        with_generated_alt: bool = True,
        respond_with: str = "content",
        token_budget: int = None
    ) -> Dict[str, Any]:
        """
        Perform a search using Jina AI Search API
        
        Args:
            query: The search query string
            num_results: Number of results to return (max 20 for Jina AI)
            search_type: Type of search ("web", "images", "news")
            provider: Search provider ("google", "bing", "reader")
            country: Country code for localized results (e.g., "us", "uk")
            language: Language code (e.g., "en", "es")
            read_content: If True, reads full content of search result pages
            with_links_summary: If True, aggregates links at the end
            with_images_summary: If True, aggregates images at the end
            with_generated_alt: If True, generates captions for images without alt text
            respond_with: Response format ("content", "markdown", "html", "text")
        
        Returns:
            Parsed response from Jina AI Search API
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if num_results < 1 or num_results > 20:
            raise ValueError("num_results must be between 1 and 20 for Jina AI Search")
        
        # Prepare request URL - using the /{q} endpoint
        url = f"{self.base_url}/{query.strip()}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        # Add content reading headers when enabled
        if read_content:
            headers["X-No-Cache"] = "true"  # Force fresh content
            headers["X-Respond-With"] = "markdown"  # Get content in markdown
        
        # Always enable link and image summaries via headers
        if with_links_summary:
            headers["X-With-Links-Summary"] = "true"
        if with_images_summary:
            headers["X-With-Images-Summary"] = "true"
        if with_generated_alt:
            headers["X-With-Generated-Alt"] = "true"
        
        params = {
            "type": search_type,
            "provider": provider,
            "num": num_results,
            "gl": country,
            "hl": language,
            "respondWith": respond_with,
            "withLinksSummary": with_links_summary,
            "withImagesSummary": with_images_summary,
            "withGeneratedAlt": with_generated_alt,
            "retainLinks": "all",  # Keep all links
            "retainImages": "all_p"  # Keep all images with generated alt text
        }
        
        if token_budget is not None:
            params["tokenBudget"] = token_budget
        
        # Add content reading capability
        if read_content:
            # When reading content, we want to get the full page content
            # Note: Don't change engine to "reader" for search - that's for direct URL reading
            if respond_with == "content":
                params["respondWith"] = "markdown"  # Better for content reading
        
        try:
            search_mode = "with content reading" if read_content else "standard"
            logger.info(f"Searching Jina AI for: '{query}' ({search_mode}) with {num_results} results using {provider}")
            
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Always expect JSON response
            data = response.json()
            
            # Check for API errors in Jina's response format
            if data.get("code") != 200:
                error_msg = data.get("data", "Unknown error")
                raise SearchError(f"Jina AI Search API error: {error_msg}")
            
            # Store the complete raw response for analysis
            search_results = data.get("data", "")
            logger.info(f"Search results type: {type(search_results)}")
            
            result = {
                "query": query,
                "results": search_results,  # Keep raw results as-is
                "raw_response": data,  # Store complete Jina response
                "metadata": {
                    "provider": provider,
                    "type": search_type,
                    "num_results": num_results,
                    "country": country,
                    "language": language,
                    "read_content": read_content,
                    "with_links_summary": with_links_summary,
                    "with_images_summary": with_images_summary,
                    "with_generated_alt": with_generated_alt,
                    "respond_with": respond_with,
                    "jina_status": data.get("status"),
                    "jina_code": data.get("code"),
                    "jina_meta": data.get("meta")
                }
            }
            
            logger.info(f"Successfully retrieved search results from Jina AI")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Search request failed: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during search: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)


# Convenience functions for different use cases
def search_jina(
    query: str, 
    num_results: int = 10,
    search_type: str = "web",
    provider: str = "google",
    country: str = "us",
    language: str = "en",
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to perform a search using default Jina AI client
    
    Args:
        query: The search query string
        num_results: Number of results to return (max 20)
        search_type: Type of search ("web", "images", "news")
        provider: Search provider ("google", "bing", "reader")
        country: Country code for localized results (e.g., "us", "uk")
        language: Language code (e.g., "en", "es")
        **kwargs: Additional options (read_content, json_mode, etc.)
    
    Returns:
        Parsed response from Jina AI Search API
    """
    client = JinaSearchClient()
    return client.search(query, num_results, search_type, provider, country, language, **kwargs)


def search_with_content(
    query: str,
    num_results: int = 5,
    provider: str = "google",
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to search AND read full content of results
    
    Args:
        query: The search query string
        num_results: Number of results to return (max 20)
        provider: Search provider ("google", "bing", "reader")
        **kwargs: Additional options
    
    Returns:
        Search results with full page content, all links, and images with captions
    """
    return search_jina(
        query=query,
        num_results=num_results,
        provider=provider,
        read_content=True,
        respond_with="markdown",
        with_links_summary=True,
        with_images_summary=True,
        with_generated_alt=True,
        **kwargs
    )


def search_structured(
    query: str,
    num_results: int = 10,
    provider: str = "google",
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to get structured JSON search results with summaries
    
    Args:
        query: The search query string
        num_results: Number of results to return (max 20)
        provider: Search provider ("google", "bing", "reader")
        **kwargs: Additional options
    
    Returns:
        Structured JSON search results with links and images summaries and captions
    """
    return search_jina(
        query=query,
        num_results=num_results,
        provider=provider,
        with_links_summary=True,
        with_images_summary=True,
        with_generated_alt=True,
        **kwargs
    )


def search_comprehensive(
    query: str,
    num_results: int = 8,
    provider: str = "google",
    **kwargs
) -> Dict[str, Any]:
    """
    Comprehensive search with ACTUAL full content reading using Jina headers
    
    Uses the "Read Full Content of SERP" feature via X-headers to:
    - Visit every URL in search results
    - Return full content using Reader
    - Include all links and images with captions
    
    Args:
        query: The search query string
        num_results: Number of results to return (max 20)
        provider: Search provider ("google", "bing", "reader")
        **kwargs: Additional options
    
    Returns:
        Complete search results with full content, links, and captioned images
    """
    return search_jina(
        query=query,
        num_results=num_results,
        provider=provider,
        read_content=True,  # This now uses X-headers for full content
        respond_with="markdown",
        with_links_summary=True,
        with_images_summary=True,
        with_generated_alt=True,
        **kwargs
    )


# Alias for backward compatibility
def search_serper(*args, **kwargs):
    """Backward compatibility alias - now uses Jina AI Search"""
    logger.warning("search_serper is deprecated, use search_jina instead")
    return search_jina(*args, **kwargs)
