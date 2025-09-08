"""Search module using Serper.dev API"""

import os
import requests
from typing import Dict, Any, Optional
from loguru import logger


class SearchError(Exception):
    """Custom exception for search-related errors"""
    pass


class SerperSearchClient:
    """Client for interacting with Serper.dev Search API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Serper Search client
        
        Args:
            api_key: Serper.dev API key. If None, will try to get from SERPER_DEV_API_KEY env var
        """
        self.api_key = api_key or os.getenv("SERPER_DEV_API_KEY")
        if not self.api_key:
            raise SearchError("SERPER_DEV_API_KEY not provided and not found in environment variables")
        
        self.base_url = "https://google.serper.dev/search"
        self.timeout = 30
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        provider: str = "google"
    ) -> Dict[str, Any]:
        """
        Perform a simple web search using Serper.dev API
        
        Args:
            query: The search query string
            num_results: Number of results to return (max 100)
            provider: Not used for Serper (always Google)
        
        Returns:
            Simple search results with title, URL, and description for each result
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if num_results < 1 or num_results > 100:
            raise ValueError("num_results must be between 1 and 100 for Serper.dev")
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query.strip(),
            "num": num_results
        }
        
        try:
            logger.info(f"Searching Serper.dev for: '{query}' with {num_results} results")
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract organic results from Serper response
            organic_results = data.get("organic", [])
            
            # Format results to match our simple interface
            formatted_results = []
            for result in organic_results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "description": result.get("snippet", "")
                })
            
            result = {
                "query": query,
                "results": formatted_results
            }
            
            logger.info(f"Successfully retrieved {len(formatted_results)} search results from Serper.dev")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Search request failed: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during search: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)


# Convenience function
def search_web(
    query: str, 
    num_results: int = 10,
    provider: str = "google"
) -> Dict[str, Any]:
    """
    Convenience function to perform a simple web search using Serper.dev
    
    Args:
        query: The search query string
        num_results: Number of results to return (max 100)
        provider: Not used (always Google via Serper.dev)
    
    Returns:
        Simple search results with title, URL, and description for each result
    """
    client = SerperSearchClient()
    return client.search(query, num_results, provider)
