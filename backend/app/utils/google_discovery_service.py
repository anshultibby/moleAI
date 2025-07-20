"""
Google Custom Search Engine (CSE) Service
Discovers Shopify stores by keyword for the hybrid search architecture
"""

import os
import requests
import json
from typing import List, Set, Dict, Any
from urllib.parse import urlparse
import time
from dotenv import load_dotenv

load_dotenv()

class GoogleDiscoveryService:
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_CSE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_CSE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID required in environment")
    
    def discover_shopify_stores(self, keyword: str, max_results: int = 100) -> List[str]:
        """
        Discover Shopify store domains using Google CSE with fallback
        Returns list of unique domain names that are actually accessible
        """
        # Phase 1: Try Google CSE discovery
        validated_domains = self._discover_via_google_cse(keyword, max_results)
        
        # Phase 2: If CSE returns too few results, add fallback domains
        if len(validated_domains) < max_results // 2:  # If we got less than half the target
            print(f"🔄 CSE returned only {len(validated_domains)} domains, adding fallback domains...")
            fallback_domains = self._get_fallback_shopify_domains(keyword)
            
            # Validate fallback domains too
            print(f"🔍 Validating {len(fallback_domains)} fallback domains...")
            validated_fallback = self._validate_discovered_domains(fallback_domains, max_results - len(validated_domains))
            
            # Combine results
            all_validated = validated_domains + validated_fallback
            
            # Remove duplicates
            unique_domains = list(dict.fromkeys(all_validated))  # Preserves order
            print(f"🎯 Combined result: {len(unique_domains)} domains ({len(validated_domains)} from CSE + {len(validated_fallback)} from fallback)")
            
            return unique_domains[:max_results]
        
        return validated_domains

    def _discover_via_google_cse(self, keyword: str, max_results: int) -> List[str]:
        """Original Google CSE discovery method"""
        domains = set()
        
        # Expanded search strategies to find diverse stores
        search_queries = [
            f"{keyword} site:myshopify.com",
            f"{keyword} inurl:collections site:myshopify.com", 
            f"{keyword} shop site:myshopify.com",
            f"buy {keyword} site:myshopify.com",
            f"{keyword} store site:myshopify.com",
            f"{keyword} online shop site:myshopify.com",
            f"best {keyword} site:myshopify.com",
            f"{keyword} boutique site:myshopify.com"
        ]
        
        # Try broader related terms too
        if len(keyword.split()) == 1:
            # For single keywords, add category expansions
            category_expansions = {
                'jacket': ['coat', 'outerwear', 'blazer'],
                'coat': ['jacket', 'outerwear', 'parka'],
                'headphones': ['earbuds', 'audio', 'sound'],
                'shoes': ['sneakers', 'boots', 'footwear'],
                'dress': ['clothing', 'fashion', 'apparel'],
                'bag': ['purse', 'handbag', 'accessories'],
                'leggings': ['pants', 'activewear', 'yoga'],
                'shirt': ['top', 'blouse', 'clothing'],
                'sweater': ['jumper', 'knitwear', 'pullover']
            }
            
            expansions = category_expansions.get(keyword.lower(), [])
            for expansion in expansions[:2]:  # Limit to avoid too many queries
                search_queries.append(f"{expansion} site:myshopify.com")
        
        print(f"🔍 Running {len(search_queries)} Google CSE queries to find diverse stores...")
        
        # Phase 1: Discover domains from Google CSE
        candidate_domains = set()
        for i, query in enumerate(search_queries):
            try:
                query_domains = self._search_query(query, max_results=20)
                candidate_domains.update(query_domains)
                
                print(f"   Query {i+1}/{len(search_queries)}: '{query}' → {len(query_domains)} candidate domains")
                
                # Rate limiting - Google CSE has limits 
                time.sleep(0.2)
                
                # Early exit if we have enough candidates for validation
                if len(candidate_domains) >= max_results * 2:  # Get 2x candidates for filtering
                    print(f"   Early exit: Found {len(candidate_domains)} candidate domains")
                    break
                
            except Exception as e:
                print(f"Error searching '{query}': {e}")
                continue
        
        print(f"📦 Discovered {len(candidate_domains)} candidate domains from Google CSE")
        
        # Phase 2: Validate domains for accessibility
        if candidate_domains:
            validated_domains = self._validate_discovered_domains(list(candidate_domains), max_results)
        else:
            validated_domains = []
        
        print(f"🎯 CSE result: {len(validated_domains)} validated, accessible stores")
        return validated_domains

    def _search_query(self, query: str, max_results: int = 20) -> Set[str]:
        """Execute a single Google CSE query and extract domains with pagination"""
        domains = set()
        
        # Google CSE allows max 10 results per request, so we need pagination
        requests_needed = min(10, (max_results + 9) // 10)  # Round up, max 10 requests (100 results)
        
        for page in range(requests_needed):
            start_index = page * 10 + 1  # Google CSE uses 1-based indexing
            
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(10, max_results - len(domains)),  # Remaining results needed
                'start': start_index,
                'fields': 'items(link,displayLink)'  # Only get what we need
            }
            
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    
                    page_domains = set()
                    for item in items:
                        domain = self._extract_shopify_domain(item.get('link', ''))
                        if domain and domain not in domains:  # Avoid duplicates
                            domains.add(domain)
                            page_domains.add(domain)
                    
                    # If no new domains found on this page, stop paginating
                    if not page_domains:
                        break
                        
                    # If we have enough domains, stop
                    if len(domains) >= max_results:
                        break
                        
                elif response.status_code == 429:
                    print(f"Rate limited on query: {query} (page {page + 1})")
                    time.sleep(1)
                    break  # Don't continue paginating if rate limited
                else:
                    print(f"Error {response.status_code} on page {page + 1}: {response.text}")
                    break
                    
            except Exception as e:
                print(f"Request failed for '{query}' page {page + 1}: {e}")
                break
            
            # Small delay between paginated requests
            if page < requests_needed - 1:
                time.sleep(0.1)
        
        return domains
    
    def _extract_shopify_domain(self, url: str) -> str:
        """Extract clean Shopify domain from URL with better validation"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Validate it's a real Shopify store
            if 'myshopify.com' in domain:
                # Extract store name (e.g., 'mystore.myshopify.com')
                store_name = domain.split('.myshopify.com')[0]
                
                # Filter out invalid/test domains - EXPANDED LIST
                invalid_domains = [
                    'example', 'test', 'demo', 'sample', 'fake', 'placeholder',
                    'localhost', '127.0.0.1', 'dev', 'staging', 'admin', 'temp',
                    'trial', 'test-store', 'demo-store', 'sample-store',
                    'default', 'null', 'undefined', 'shop-test', 'test-shop'
                ]
                
                # Check exact matches and partial matches
                if store_name in invalid_domains or any(invalid in store_name for invalid in invalid_domains):
                    print(f"   🚫 Filtered invalid domain: {domain} (contains: {store_name})")
                    return None
                
                # Ensure it's a reasonable store name (not just numbers or very short)
                if len(store_name) < 3 or store_name.isdigit() or store_name.replace('-', '').isdigit():
                    print(f"   🚫 Filtered unreasonable domain: {domain} (store name: {store_name})")
                    return None
                
                return domain
            
            # Also handle custom domains that redirect to Shopify
            # But be more selective - only if we can verify it's actually Shopify
            # For now, stick to myshopify.com domains only to avoid false positives
            
        except Exception as e:
            print(f"   ⚠️  Error parsing URL {url}: {e}")
        
        return None

    def discover_with_categories(self, base_keyword: str, categories: List[str]) -> Dict[str, List[str]]:
        """
        Discover stores across multiple product categories
        Returns dict of {category: [domains]}
        """
        results = {}
        
        for category in categories:
            keyword = f"{base_keyword} {category}"
            domains = self.discover_shopify_stores(keyword, max_results=20)
            results[category] = domains
            
            print(f"Category '{category}': found {len(domains)} stores")
            
            # Rate limiting between categories
            time.sleep(0.5)
        
        return results
    
    def get_store_info(self, domain: str) -> Dict[str, Any]:
        """
        Get basic information about a Shopify store
        """
        try:
            # Try to access the store's basic info
            store_url = f"https://{domain}"
            
            # Basic validation that store exists and is accessible
            response = requests.head(store_url, timeout=5)
            
            return {
                'domain': domain,
                'url': store_url,
                'accessible': response.status_code == 200,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'domain': domain,
                'url': f"https://{domain}",
                'accessible': False,
                'error': str(e)
            }

    def _validate_discovered_domains(self, candidate_domains: List[str], max_results: int) -> List[str]:
        """Validate that discovered domains are actually accessible Shopify stores"""
        import requests
        
        print(f"🔍 Validating {len(candidate_domains)} discovered domains...")
        print(f"📋 Candidate domains: {candidate_domains}")
        
        validated_domains = []
        filtered_domains = {
            'connection_failed': [],
            'not_accessible': [],
            'timeout': [],
            'other_errors': []
        }
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        for i, domain in enumerate(candidate_domains):
            if len(validated_domains) >= max_results:
                print(f"   ✋ Stopping validation - reached max_results ({max_results})")
                break
                
            try:
                # Test products.json endpoint (most reliable test for Shopify)
                test_url = f"https://{domain}/products.json"
                response = session.head(test_url, timeout=8)  # Increased timeout
                
                if response.status_code in [200, 301, 302]:
                    validated_domains.append(domain)
                    print(f"   ✅ {i+1}/{len(candidate_domains)}: {domain} - ACCESSIBLE ({response.status_code})")
                else:
                    filtered_domains['not_accessible'].append((domain, response.status_code))
                    print(f"   ❌ {i+1}/{len(candidate_domains)}: {domain} - NOT ACCESSIBLE ({response.status_code})")
                
            except requests.exceptions.ConnectionError as e:
                filtered_domains['connection_failed'].append((domain, str(e)))
                print(f"   ❌ {i+1}/{len(candidate_domains)}: {domain} - CONNECTION FAILED: {e}")
            except requests.exceptions.Timeout as e:
                filtered_domains['timeout'].append((domain, str(e)))
                print(f"   ⏰ {i+1}/{len(candidate_domains)}: {domain} - TIMEOUT: {e}")
            except Exception as e:
                filtered_domains['other_errors'].append((domain, str(e)))
                print(f"   ❌ {i+1}/{len(candidate_domains)}: {domain} - ERROR: {e}")
            
            # Rate limiting to be respectful
            time.sleep(0.2)  # Slightly faster
        
        # Detailed filtering summary
        total_filtered = sum(len(filtered_list) for filtered_list in filtered_domains.values())
        print(f"\n📊 Filtering Summary:")
        print(f"   ✅ Validated: {len(validated_domains)}")
        print(f"   🚫 Filtered out: {total_filtered}")
        
        if filtered_domains['connection_failed']:
            print(f"   🔌 Connection failed ({len(filtered_domains['connection_failed'])}):")
            for domain, error in filtered_domains['connection_failed'][:3]:  # Show first 3
                print(f"      - {domain}: {error}")
            if len(filtered_domains['connection_failed']) > 3:
                print(f"      ... and {len(filtered_domains['connection_failed']) - 3} more")
        
        if filtered_domains['not_accessible']:
            print(f"   🚫 Not accessible ({len(filtered_domains['not_accessible'])}):")
            for domain, status in filtered_domains['not_accessible'][:3]:  # Show first 3
                print(f"      - {domain}: HTTP {status}")
            if len(filtered_domains['not_accessible']) > 3:
                print(f"      ... and {len(filtered_domains['not_accessible']) - 3} more")
        
        if filtered_domains['timeout']:
            print(f"   ⏰ Timeouts ({len(filtered_domains['timeout'])}):")
            for domain, error in filtered_domains['timeout'][:3]:  # Show first 3
                print(f"      - {domain}")
            if len(filtered_domains['timeout']) > 3:
                print(f"      ... and {len(filtered_domains['timeout']) - 3} more")
        
        # Check for potentially over-filtered domains
        potentially_valid = []
        for domain, status in filtered_domains['not_accessible']:
            if status in [403, 401, 503]:  # These might be temporarily blocked but valid stores
                potentially_valid.append((domain, status))
        
        if potentially_valid:
            print(f"   ⚠️  Potentially over-filtered ({len(potentially_valid)} domains with 403/401/503):")
            for domain, status in potentially_valid[:3]:
                print(f"      - {domain}: HTTP {status} (might be blocking bots but is a valid store)")
        
        print(f"✅ Final: {len(validated_domains)} domains validated as accessible")
        return validated_domains

    def _get_fallback_shopify_domains(self, keyword: str) -> List[str]:
        """Get fallback domains when CSE doesn't return enough results"""
        
        # Curated list of known working Shopify domains by category
        fallback_domains = {
            'clothing': [
                'shop.gymshark.com', 'shop.bombas.com', 'shop.allbirds.com',
                'skims.myshopify.com', 'fenty.myshopify.com', 'shop.glossier.com'
            ],
            'fashion': [
                'shop.gymshark.com', 'skims.myshopify.com', 'fenty.myshopify.com',
                'shop.bombas.com', 'shop.allbirds.com'
            ],
            'shoes': [
                'shop.allbirds.com', 'shop.gymshark.com', 'vans.myshopify.com'
            ],
            'beauty': [
                'shop.glossier.com', 'fenty.myshopify.com', 'rare-beauty.myshopify.com'
            ],
            'fitness': [
                'shop.gymshark.com', 'shop.bombas.com', 'shop.allbirds.com'
            ],
            'accessories': [
                'shop.bombas.com', 'shop.allbirds.com', 'shop.glossier.com'
            ]
        }
        
        # Try to match keyword to categories
        keyword_lower = keyword.lower()
        relevant_domains = []
        
        for category, domains in fallback_domains.items():
            if any(word in keyword_lower for word in category.split()) or keyword_lower in category:
                relevant_domains.extend(domains)
        
        # If no category match, use general clothing/fashion domains
        if not relevant_domains:
            relevant_domains = fallback_domains['clothing']
        
        # Remove duplicates while preserving order
        unique_domains = list(dict.fromkeys(relevant_domains))
        
        print(f"📋 Using {len(unique_domains)} fallback domains for keyword '{keyword}'")
        return unique_domains


# Convenience functions
def discover_stores_for_keyword(keyword: str, max_results: int = 30) -> List[str]:
    """Quick function to discover stores for a keyword"""
    try:
        discovery = GoogleDiscoveryService()
        return discovery.discover_shopify_stores(keyword, max_results)
    except Exception as e:
        print(f"Discovery failed: {e}")
        return []

def discover_kids_clothing_stores() -> List[str]:
    """Specialized function for kids clothing discovery"""
    keywords = [
        "kids clothes",
        "children clothing", 
        "kids shoes",
        "baby clothes",
        "toddler clothes"
    ]
    
    all_stores = set()
    discovery = GoogleDiscoveryService()
    
    for keyword in keywords:
        stores = discovery.discover_shopify_stores(keyword, max_results=10)
        all_stores.update(stores)
        print(f"Keyword '{keyword}': {len(stores)} stores")
    
    return list(all_stores) 