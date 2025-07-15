"""
Firecrawl Service for Product Search
Handles web scraping and product search using Firecrawl API
"""

import requests
import json
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class FirecrawlService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search_products(self, query: str, max_price: Optional[float] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for products on Zara using Firecrawl and return full content for LLM processing
        """
        if not self.api_key:
            raise ValueError("Firecrawl API key not configured")
        
        try:
            print(f"Searching Zara for '{query}'...")
            
            # Build Zara search URL
            search_url = self._build_zara_search_url(query)
            print(f"Search URL: {search_url}")
            
            # Scrape the search results
            scraped_data = self._scrape_url(search_url)
            
            if scraped_data and 'data' in scraped_data:
                # Return the full content for LLM processing
                content = {
                    'source': 'zara.com',
                    'query': query,
                    'url': search_url,
                    'markdown': scraped_data['data'].get('markdown', ''),
                    'metadata': scraped_data['data'].get('metadata', {})
                }
                
                print(f"✅ Successfully scraped Zara search results")
                return [content]
            else:
                print("⚠️ No data returned from Zara")
                return []
                
        except Exception as e:
            print(f"❌ Error searching Zara: {str(e)}")
            return []
    
    def _build_zara_search_url(self, query: str) -> str:
        """
        Build search URL for Zara
        """
        # Clean and encode the query
        query_encoded = query.replace(" ", "%20")
        
        # Zara search URL format
        return f"https://www.zara.com/us/en/search?searchTerm={query_encoded}"
    
    def _scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Use Firecrawl to scrape a URL and return markdown content
        """
        try:
            payload = {
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "timeout": 20000,
                "waitFor": 3000  # Wait for dynamic content to load
            }
            
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=self.headers,
                json=payload,
                timeout=25
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Firecrawl API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"Timeout error scraping URL {url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error scraping URL {url}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping URL {url}: {str(e)}")
            return None 