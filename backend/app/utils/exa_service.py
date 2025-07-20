"""
Exa.ai Search Service
High-quality web search and content retrieval using Exa.ai
"""

import os
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ExaSearchResult:
    """Represents a single search result from Exa"""
    title: str
    url: str
    text: Optional[str] = None
    highlights: Optional[List[str]] = None
    published_date: Optional[str] = None
    score: Optional[float] = None


class ExaService:
    """Service for interacting with Exa.ai API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('EXA_API_KEY')
        if not self.api_key:
            raise ValueError("EXA_API_KEY is required")
        
        self.base_url = "https://api.exa.ai"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        start_crawl_date: Optional[str] = None,
        end_crawl_date: Optional[str] = None,
        start_published_date: Optional[str] = None,
        end_published_date: Optional[str] = None,
        use_autoprompt: bool = True,
        type: str = "neural",
        category: Optional[str] = None,
        include_text: bool = True,
        text_type: str = "text",
        highlights_per_url: int = 3
    ) -> List[ExaSearchResult]:
        """
        Perform a search using Exa.ai
        
        Args:
            query: The search query
            num_results: Number of results to return (max 1000)
            include_domains: List of domains to include in search
            exclude_domains: List of domains to exclude from search
            start_crawl_date: Start date for crawl date filter (YYYY-MM-DD)
            end_crawl_date: End date for crawl date filter (YYYY-MM-DD)
            start_published_date: Start date for published date filter (YYYY-MM-DD)
            end_published_date: End date for published date filter (YYYY-MM-DD)
            use_autoprompt: Whether to use Exa's autoprompt feature
            type: Search type ("neural" or "keyword")
            category: Content category filter
            include_text: Whether to include text content
            text_type: Type of text to include ("text" or "highlights")
            highlights_per_url: Number of highlights per URL
        
        Returns:
            List of ExaSearchResult objects
        """
        url = f"{self.base_url}/search"
        
        # Build request payload
        payload = {
            "query": query,
            "numResults": num_results,
            "useAutoprompt": use_autoprompt,
            "type": type,
            "contents": {
                "text": {
                    "includeHtmlTags": False,
                    "maxCharacters": 8000
                } if include_text and text_type == "text" else None,
                "highlights": {
                    "numSentences": highlights_per_url,
                    "highlightsPerUrl": highlights_per_url
                } if include_text and text_type == "highlights" else None
            }
        }
        
        # Add optional filters
        if include_domains:
            payload["includeDomains"] = include_domains
        if exclude_domains:
            payload["excludeDomains"] = exclude_domains
        if start_crawl_date:
            payload["startCrawlDate"] = start_crawl_date
        if end_crawl_date:
            payload["endCrawlDate"] = end_crawl_date
        if start_published_date:
            payload["startPublishedDate"] = start_published_date
        if end_published_date:
            payload["endPublishedDate"] = end_published_date
        if category:
            payload["category"] = category
        
        # Remove None values from contents
        if payload["contents"]["text"] is None and payload["contents"]["highlights"] is None:
            del payload["contents"]
        elif payload["contents"]["text"] is None:
            del payload["contents"]["text"]
        elif payload["contents"]["highlights"] is None:
            del payload["contents"]["highlights"]
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("results", []):
                result = ExaSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    text=item.get("text", ""),
                    highlights=item.get("highlights", []),
                    published_date=item.get("publishedDate"),
                    score=item.get("score")
                )
                results.append(result)
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling Exa API: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in Exa search: {e}")
            return []
    
    def search_shopping_sites(
        self,
        product_query: str,
        num_results: int = 10,
        max_price: Optional[float] = None
    ) -> List[ExaSearchResult]:
        """
        Search for products across shopping sites using Exa.ai
        
        Args:
            product_query: The product to search for
            num_results: Number of results to return
            max_price: Maximum price filter (if supported)
        
        Returns:
            List of ExaSearchResult objects from shopping sites
        """
        # Common shopping domains
        shopping_domains = [
            "amazon.com",
            "amazon.co.uk", 
            "amazon.ca",
            "ebay.com",
            "target.com",
            "walmart.com",
            "bestbuy.com",
            "newegg.com",
            "costco.com",
            "homedepot.com",
            "lowes.com",
            "macys.com",
            "nordstrom.com",
            "zappos.com",
            "etsy.com",
            "wayfair.com",
            "overstock.com",
            "alibaba.com",
            "shopify.com"
        ]
        
        # Build search query for shopping
        search_query = f"{product_query} price buy online"
        if max_price:
            search_query += f" under ${max_price}"
        
        return self.search(
            query=search_query,
            num_results=num_results,
            include_domains=shopping_domains,
            type="neural",
            include_text=True,
            text_type="text"
        )
    
    def search_specific_stores(
        self,
        product_query: str,
        store_domains: List[str],
        num_results: int = 5
    ) -> List[ExaSearchResult]:
        """
        Search for products on specific store domains
        
        Args:
            product_query: The product to search for
            store_domains: List of specific store domains to search
            num_results: Number of results per store
        
        Returns:
            List of ExaSearchResult objects
        """
        search_query = f"{product_query} price buy"
        
        return self.search(
            query=search_query,
            num_results=num_results,
            include_domains=store_domains,
            type="neural",
            include_text=True,
            text_type="text"
        )
    
    def get_content(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Get full content for specific URLs using Exa's contents endpoint
        
        Args:
            urls: List of URLs to get content for
        
        Returns:
            List of content data
        """
        url = f"{self.base_url}/contents"
        
        payload = {
            "ids": urls,
            "contents": {
                "text": {
                    "includeHtmlTags": False,
                    "maxCharacters": 10000
                }
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            return response.json().get("contents", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting content from Exa API: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error getting content: {e}")
            return []


# Convenience functions
def search_products_with_exa(
    query: str,
    api_key: str = None,
    num_results: int = 10,
    max_price: Optional[float] = None,
    specific_stores: Optional[List[str]] = None
) -> List[ExaSearchResult]:
    """
    Convenience function to search for products using Exa.ai
    
    Args:
        query: Product search query
        api_key: Exa API key (optional, will use env var if not provided)
        num_results: Number of results to return
        max_price: Maximum price filter
        specific_stores: List of specific store domains to search
    
    Returns:
        List of ExaSearchResult objects
    """
    service = ExaService(api_key)
    
    if specific_stores:
        return service.search_specific_stores(query, specific_stores, num_results)
    else:
        return service.search_shopping_sites(query, num_results, max_price)


def search_web_with_exa(
    query: str,
    api_key: str = None,
    num_results: int = 10,
    **kwargs
) -> List[ExaSearchResult]:
    """
    Convenience function for general web search using Exa.ai
    
    Args:
        query: Search query
        api_key: Exa API key (optional, will use env var if not provided)
        num_results: Number of results to return
        **kwargs: Additional search parameters
    
    Returns:
        List of ExaSearchResult objects
    """
    service = ExaService(api_key)
    return service.search(query, num_results, **kwargs) 