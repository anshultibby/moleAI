"""
Web Search Service for Product Search
Handles web scraping and product search using Google search + Firecrawl API for dynamic site discovery
"""

import requests
import json
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
import urllib.parse
import re

load_dotenv()

class FirecrawlService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Popular e-commerce sites to prioritize (fallback)
        self.known_ecommerce_sites = [
            {
                "name": "Zara",
                "domain": "zara.com",
                "search_url_template": "https://www.zara.com/us/en/search?searchTerm={query}",
                "priority": 1
            },
            {
                "name": "H&M",
                "domain": "hm.com", 
                "search_url_template": "https://www2.hm.com/en_us/search-results.html?q={query}",
                "priority": 2
            },
            {
                "name": "Uniqlo",
                "domain": "uniqlo.com",
                "search_url_template": "https://www.uniqlo.com/us/en/search?q={query}",
                "priority": 3
            },
            {
                "name": "Forever 21",
                "domain": "forever21.com",
                "search_url_template": "https://www.forever21.com/us/2000444103.html?q={query}",
                "priority": 4
            },
            {
                "name": "ASOS",
                "domain": "asos.com",
                "search_url_template": "https://www.asos.com/us/search/?q={query}",
                "priority": 5
            }
        ]
    
    def search_products_via_google(self, query: str, max_price: Optional[float] = None, category: Optional[str] = None, max_sites: int = 5) -> List[Dict[str, Any]]:
        """
        Search for products by first using Google to find relevant shopping sites, then scraping those sites
        """
        if not self.api_key:
            raise ValueError("Firecrawl API key not configured")
        
        print(f"🔍 Using Google to find shopping sites for '{query}'...")
        
        # Step 1: Search Google for shopping results
        shopping_sites = self._search_google_for_shopping_sites(query, max_sites)
        
        if not shopping_sites:
            print("⚠️ No shopping sites found via Google, falling back to known sites")
            return self.search_products_known_sites(query, max_price, category, max_sites)
        
        # Step 2: Scrape the found shopping sites
        all_results = []
        for site_info in shopping_sites[:max_sites]:
            try:
                print(f"🕷️ Scraping {site_info['domain']} for '{query}'...")
                
                scraped_data = self._scrape_url(site_info['url'])
                
                if scraped_data and 'data' in scraped_data:
                    content = {
                        'source': site_info['domain'],
                        'store_name': site_info['store_name'],
                        'query': query,
                        'url': site_info['url'],
                        'markdown': scraped_data['data'].get('markdown', ''),
                        'metadata': scraped_data['data'].get('metadata', {}),
                        'priority': site_info.get('priority', 999)
                    }
                    
                    print(f"✅ Successfully scraped {site_info['store_name']}")
                    all_results.append(content)
                else:
                    print(f"⚠️ No data returned from {site_info['store_name']}")
                    
            except Exception as e:
                print(f"❌ Error scraping {site_info['store_name']}: {str(e)}")
                continue
        
        return all_results
    
    def _search_google_for_shopping_sites(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Use Firecrawl to search Google for shopping sites related to the query
        """
        try:
            # Create a Google search query focused on shopping
            search_terms = [
                f"{query} buy online store",
                f"{query} shopping purchase",
                f"buy {query} online store"
            ]
            
            all_sites = []
            
            for search_term in search_terms[:2]:  # Limit to 2 search terms to avoid too many requests
                google_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_term)}"
                print(f"🔍 Searching Google: {search_term}")
                
                scraped_data = self._scrape_url(google_url)
                
                if scraped_data and 'data' in scraped_data:
                    markdown_content = scraped_data['data'].get('markdown', '')
                    sites = self._extract_shopping_sites_from_google_results(markdown_content, query)
                    all_sites.extend(sites)
                    
                    if len(all_sites) >= max_results:
                        break
            
            # Remove duplicates and prioritize known e-commerce sites
            unique_sites = self._deduplicate_and_prioritize_sites(all_sites)
            
            return unique_sites[:max_results]
            
        except Exception as e:
            print(f"❌ Error searching Google: {str(e)}")
            return []
    
    def _extract_shopping_sites_from_google_results(self, markdown_content: str, query: str) -> List[Dict[str, Any]]:
        """
        Extract shopping site URLs from Google search results markdown
        """
        sites = []
        
        # Common e-commerce domains to look for
        ecommerce_domains = [
            'amazon.com', 'ebay.com', 'etsy.com', 'shopify.com', 'woocommerce.com',
            'zara.com', 'hm.com', 'uniqlo.com', 'forever21.com', 'asos.com',
            'nordstrom.com', 'macys.com', 'target.com', 'walmart.com', 'costco.com',
            'overstock.com', 'wayfair.com', 'alibaba.com', 'aliexpress.com',
            'shopstyle.com', 'net-a-porter.com', 'ssense.com', 'farfetch.com',
            'revolve.com', 'nastygal.com', 'boohoo.com', 'prettylittlething.com',
            'fashionnova.com', 'shein.com', 'yesstyle.com', 'zaful.com'
        ]
        
        # Extract URLs from markdown that match e-commerce patterns
        url_pattern = r'https?://(?:www\.)?([^/\s\)]+)'
        urls = re.findall(url_pattern, markdown_content)
        
        for url_domain in urls:
            # Clean domain
            domain = url_domain.lower().strip()
            
            # Check if it's a known e-commerce domain
            for ecom_domain in ecommerce_domains:
                if ecom_domain in domain:
                    # Try to build a search URL for this domain
                    search_url = self._build_search_url_for_domain(domain, query)
                    if search_url:
                        store_name = self._extract_store_name_from_domain(domain)
                        
                        site_info = {
                            'domain': domain,
                            'store_name': store_name,
                            'url': search_url,
                            'priority': self._get_priority_for_domain(domain)
                        }
                        
                        # Avoid duplicates
                        if not any(s['domain'] == domain for s in sites):
                            sites.append(site_info)
                    break
        
        return sites
    
    def _build_search_url_for_domain(self, domain: str, query: str) -> Optional[str]:
        """
        Build a search URL for a given domain
        """
        query_encoded = urllib.parse.quote_plus(query)
        
        # Known search URL patterns
        search_patterns = {
            'amazon.com': f'https://www.amazon.com/s?k={query_encoded}',
            'ebay.com': f'https://www.ebay.com/sch/i.html?_nkw={query_encoded}',
            'etsy.com': f'https://www.etsy.com/search?q={query_encoded}',
            'zara.com': f'https://www.zara.com/us/en/search?searchTerm={query_encoded}',
            'hm.com': f'https://www2.hm.com/en_us/search-results.html?q={query_encoded}',
            'uniqlo.com': f'https://www.uniqlo.com/us/en/search?q={query_encoded}',
            'forever21.com': f'https://www.forever21.com/us/2000444103.html?q={query_encoded}',
            'asos.com': f'https://www.asos.com/us/search/?q={query_encoded}',
            'nordstrom.com': f'https://www.nordstrom.com/sr?keyword={query_encoded}',
            'macys.com': f'https://www.macys.com/shop/featured/{query_encoded}',
            'target.com': f'https://www.target.com/s?searchTerm={query_encoded}',
            'walmart.com': f'https://www.walmart.com/search/?query={query_encoded}',
            'net-a-porter.com': f'https://www.net-a-porter.com/en-us/search/?q={query_encoded}',
            'ssense.com': f'https://www.ssense.com/en-us/search?q={query_encoded}',
            'farfetch.com': f'https://www.farfetch.com/shopping/search/items.aspx?q={query_encoded}',
            'revolve.com': f'https://www.revolve.com/search/?search={query_encoded}',
            'shein.com': f'https://us.shein.com/search.html?q={query_encoded}',
        }
        
        for known_domain, search_url in search_patterns.items():
            if known_domain in domain:
                return search_url
        
        # Generic fallback patterns
        if 'shopify' in domain:
            return f'https://{domain}/search?q={query_encoded}'
        
        # Try common search patterns
        common_patterns = [
            f'https://{domain}/search?q={query_encoded}',
            f'https://{domain}/search?query={query_encoded}',
            f'https://{domain}/s?k={query_encoded}',
        ]
        
        return common_patterns[0]  # Return the first common pattern as fallback
    
    def _extract_store_name_from_domain(self, domain: str) -> str:
        """
        Extract a readable store name from domain
        """
        # Remove common prefixes/suffixes
        name = domain.replace('www.', '').replace('.com', '').replace('.co.uk', '').replace('.net', '')
        
        # Special cases
        name_mapping = {
            'hm': 'H&M',
            'net-a-porter': 'Net-A-Porter',
            'prettylittlething': 'PrettyLittleThing',
            'nastygal': 'Nasty Gal',
            'fashionnova': 'Fashion Nova',
            'yesstyle': 'YesStyle',
        }
        
        if name in name_mapping:
            return name_mapping[name]
        
        # Capitalize first letter of each word
        return ' '.join(word.capitalize() for word in name.replace('-', ' ').replace('_', ' ').split())
    
    def _get_priority_for_domain(self, domain: str) -> int:
        """
        Get priority for a domain (lower = higher priority)
        """
        priority_mapping = {
            'zara.com': 1,
            'hm.com': 2,
            'uniqlo.com': 3,
            'forever21.com': 4,
            'asos.com': 5,
            'amazon.com': 6,
            'nordstrom.com': 7,
            'macys.com': 8,
            'target.com': 9,
            'net-a-porter.com': 10,
        }
        
        for known_domain, priority in priority_mapping.items():
            if known_domain in domain:
                return priority
        
        return 999  # Default low priority for unknown domains
    
    def _deduplicate_and_prioritize_sites(self, sites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate sites and sort by priority
        """
        # Remove duplicates based on domain
        seen_domains = set()
        unique_sites = []
        
        for site in sites:
            domain = site['domain']
            if domain not in seen_domains:
                seen_domains.add(domain)
                unique_sites.append(site)
        
        # Sort by priority (lower number = higher priority)
        unique_sites.sort(key=lambda x: x.get('priority', 999))
        
        return unique_sites
    
    def search_products_known_sites(self, query: str, max_price: Optional[float] = None, category: Optional[str] = None, max_sites: int = 3) -> List[Dict[str, Any]]:
        """
        Fallback method: Search products using known e-commerce sites
        """
        sites_to_search = self.known_ecommerce_sites[:max_sites]
        all_results = []
        
        for site in sites_to_search:
            try:
                print(f"Searching {site['name']} for '{query}'...")
                
                # Build search URL for this site
                search_url = self._build_search_url(query, site)
                print(f"Search URL: {search_url}")
                
                # Scrape the search results
                scraped_data = self._scrape_url(search_url)
                    
                if scraped_data and 'data' in scraped_data:
                    # Return the full content for LLM processing
                    content = {
                        'source': site['domain'],
                        'store_name': site['name'],
                        'query': query,
                        'url': search_url,
                        'markdown': scraped_data['data'].get('markdown', ''),
                        'metadata': scraped_data['data'].get('metadata', {}),
                        'priority': site['priority']
                    }
                    
                    print(f"✅ Successfully scraped {site['name']} search results")
                    all_results.append(content)
                else:
                    print(f"⚠️ No data returned from {site['name']}")
                        
            except Exception as e:
                print(f"❌ Error searching {site['name']}: {str(e)}")
                continue
        
        return all_results
    
    def search_products(self, query: str, max_price: Optional[float] = None, category: Optional[str] = None, sites: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Main method: Search for products using Google discovery or known sites
        """
        if not self.api_key:
            raise ValueError("Firecrawl API key not configured")
        
        # If specific sites are requested, use the known sites method
        if sites:
            return self._search_specific_sites(query, sites, max_price, category)
        
        # Otherwise, use Google discovery
        try:
            return self.search_products_via_google(query, max_price, category)
        except Exception as e:
            print(f"⚠️ Google search failed: {str(e)}, falling back to known sites")
            return self.search_products_known_sites(query, max_price, category)
    
    def _search_specific_sites(self, query: str, sites: List[str], max_price: Optional[float] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search specific requested sites
        """
        requested_sites = []
        for site_name in sites:
            for site in self.known_ecommerce_sites:
                if site_name.lower() in site['name'].lower() or site_name.lower() in site['domain'].lower():
                    requested_sites.append(site)
                    break
        
        if not requested_sites:
            return []
        
        all_results = []
        for site in requested_sites:
            try:
                search_url = self._build_search_url(query, site)
                scraped_data = self._scrape_url(search_url)
                
                if scraped_data and 'data' in scraped_data:
                    content = {
                        'source': site['domain'],
                        'store_name': site['name'],
                        'query': query,
                        'url': search_url,
                        'markdown': scraped_data['data'].get('markdown', ''),
                        'metadata': scraped_data['data'].get('metadata', {}),
                        'priority': site['priority']
                    }
                    all_results.append(content)
            except Exception as e:
                print(f"❌ Error searching {site['name']}: {str(e)}")
                continue
        
        return all_results
    
    def _build_search_url(self, query: str, site: Dict[str, Any]) -> str:
        """
        Build search URL for a specific known site
        """
        query_encoded = urllib.parse.quote_plus(query)
        return site['search_url_template'].format(query=query_encoded)
    
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