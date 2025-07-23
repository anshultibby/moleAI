"""Simple Google Custom Search service for discovering e-commerce stores"""

import os
from typing import List, Dict, Any
import requests
from dataclasses import dataclass
from .debug_logger import debug_log, log_execution

@dataclass
class StoreResult:
    """Represents a discovered store"""
    domain: str
    title: str
    description: str
    has_products_json: bool = False

class GoogleCSEService:
    """Simple service for discovering stores using Google Custom Search"""
    
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_CSE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_CSE_ID")
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID required")
            
        debug_log(f"CSE Service initialized with engine ID: {self.search_engine_id}")
    
    @log_execution
    def discover_stores(self, query: str, max_results: int = 10) -> List[StoreResult]:
        """
        Discover e-commerce stores for a given query
        Returns list of store domains with basic info
        """
        stores = []
        
        try:
            # Do a single clean search
            debug_log(f"CSE searching for: {query}")
            results = self._search_google_cse(query)
            debug_log(f"Got {len(results)} raw results")
            
            for result in results:
                try:
                    domain = self._extract_domain(result.get('link', ''))
                    if not domain:
                        continue
                        
                    debug_log(f"Processing domain: {domain}")
                    
                    # Check if store has products.json
                    has_json = self._check_products_json(domain)
                    debug_log(f"products.json check: {'✓' if has_json else '✗'}")
                    
                    stores.append(StoreResult(
                        domain=domain,
                        title=result.get('title', ''),
                        description=result.get('snippet', ''),
                        has_products_json=has_json
                    ))
                    debug_log(f"Added store: {domain}")
                    
                    if len(stores) >= max_results:
                        break
                        
                except Exception as e:
                    debug_log(f"Error processing result: {e}")
                    continue
                    
        except Exception as e:
            debug_log(f"Error in CSE search: {e}")
        
        debug_log(f"Found {len(stores)} stores with products.json")
        return stores
    
    @log_execution
    def _search_google_cse(self, query: str) -> List[Dict[str, Any]]:
        """Execute a Google CSE query"""
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Add clothing and e-commerce focused terms
        search_query = f"clothing store {query} site:myshopify.com"
        
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': search_query,
            'num': 10,  # Max allowed per request
            'siteSearch': '.myshopify.com',
            'siteSearchFilter': 'i',  # Include only these sites
            # Add clothing-focused terms
            'exactTerms': 'clothing|apparel|fashion|dress|dresses|coat|coats',
            'excludeTerms': 'furniture|tools|equipment|hardware|food|beauty|hair|jewelry'
        }
        
        debug_log(f"CSE params: {params}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        debug_log(f"CSE response status: {data.get('searchInformation', {}).get('totalResults', 'unknown')} results")
        
        return data.get('items', [])
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Convert to myshopify domain if needed
            if 'myshopify.com' not in domain and '.shopify.com' in domain:
                domain = domain.replace('.shopify.com', '.myshopify.com')
            return domain
        except:
            return ""
    
    def _check_products_json(self, domain: str) -> bool:
        """Check if domain has products.json endpoint"""
        try:
            url = f"https://{domain}/products.json?limit=1"
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except:
            return False 