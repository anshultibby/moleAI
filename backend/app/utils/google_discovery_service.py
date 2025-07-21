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
from datetime import datetime, timedelta

# Import progress streaming function
from .progress_utils import stream_progress_update

load_dotenv()

# Domain validation cache - shared across all instances
_DOMAIN_CACHE = {}
_CACHE_FILE = os.path.join("backend", "domain_validation_cache.json")  # Save in backend directory
_CACHE_DURATION_HOURS = 24  # Cache valid domains for 24 hours

def _load_domain_cache():
    """Load domain validation cache from file"""
    global _DOMAIN_CACHE
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                # Convert string timestamps back to datetime objects
                for domain, data in cache_data.items():
                    if 'validated_at' in data:
                        data['validated_at'] = datetime.fromisoformat(data['validated_at'])
                _DOMAIN_CACHE = cache_data
                print(f"📁 Loaded domain cache with {len(_DOMAIN_CACHE)} entries")
    except Exception as e:
        print(f"⚠️  Could not load domain cache: {e}")
        _DOMAIN_CACHE = {}

def _save_domain_cache():
    """Save domain validation cache to file"""
    try:
        # Convert datetime objects to strings for JSON serialization
        cache_data = {}
        for domain, data in _DOMAIN_CACHE.items():
            cache_data[domain] = data.copy()
            if 'validated_at' in cache_data[domain]:
                cache_data[domain]['validated_at'] = cache_data[domain]['validated_at'].isoformat()
        
        with open(_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save domain cache: {e}")

def _is_cache_valid(domain: str) -> bool:
    """Check if a domain's cache entry is still valid"""
    if domain not in _DOMAIN_CACHE:
        return False
    
    cached_data = _DOMAIN_CACHE[domain]
    if 'validated_at' not in cached_data:
        return False
    
    # Check if cache is expired
    cache_age = datetime.now() - cached_data['validated_at']
    return cache_age < timedelta(hours=_CACHE_DURATION_HOURS)

def _get_cached_domains(candidate_domains: List[str]) -> tuple[List[str], List[str]]:
    """
    Split domains into cached (valid) and uncached (need validation)
    Returns: (cached_valid_domains, uncached_domains)
    """
    cached_valid = []
    uncached = []
    
    for domain in candidate_domains:
        if _is_cache_valid(domain) and _DOMAIN_CACHE[domain].get('is_valid', False):
            cached_valid.append(domain)
        else:
            uncached.append(domain)
    
    return cached_valid, uncached

def _cache_domain_result(domain: str, is_valid: bool, status_code: int = None, error: str = None):
    """Cache the validation result for a domain"""
    _DOMAIN_CACHE[domain] = {
        'is_valid': is_valid,
        'validated_at': datetime.now(),
        'status_code': status_code,
        'error': error
    }

# Load cache on module import
_load_domain_cache()


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
        print(f"🔍 Discovering Shopify stores for '{keyword}'...")
        
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
        
        print(f"✅ Discovery complete: {len(validated_domains)} stores found")
        return validated_domains

    def _discover_via_google_cse(self, keyword: str, max_results: int) -> List[str]:
        """Original Google CSE discovery method"""
        domains = set()
        
        # Expanded search strategies to find diverse stores
        search_queries = [
            f"{keyword}",
            f"{keyword} inurl:collections", 
            f"{keyword} shop",
            f"buy {keyword}",
            f"{keyword} store",
            f"{keyword} online shop",
            f"best {keyword}",
            f"{keyword} boutique"
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
                search_queries.append(f"{expansion}")
        
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
        """Validate that discovered domains are actually accessible Shopify stores with caching"""
        import requests
        
        # Check cache first to avoid repeated validation
        cached_valid, uncached_domains = _get_cached_domains(candidate_domains)
        
        print(f"🔍 Validating {len(candidate_domains)} discovered domains...")
        if cached_valid:
            print(f"📁 Using {len(cached_valid)} cached valid domains")
            stream_progress_update(f"📁 **Cached domains:** {', '.join([f'*{domain}*' for domain in cached_valid[:10]])}")
        
        if uncached_domains:
            print(f"⏱️  Validating {len(uncached_domains)} new domains (may take 5-10 seconds)...")
        else:
            print(f"✅ All domains found in cache!")
        
        validated_domains = cached_valid.copy()  # Start with cached valid domains
        
        if not uncached_domains:
            # All domains were cached, return up to max_results
            final_domains = validated_domains[:max_results]
            print(f"📊 Validation complete: {len(final_domains)} domains (all from cache)")
            return final_domains
        
        # Validate only uncached domains
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
        
        # Show progress every 5 domains
        progress_interval = 5
        
        for i, domain in enumerate(uncached_domains):
            if len(validated_domains) >= max_results:
                print(f"   ✋ Stopping validation - reached max_results ({max_results})")
                break
            
            # Show progress
            if (i + 1) % progress_interval == 0 or i == 0:
                print(f"   📊 Progress: {i+1}/{len(uncached_domains)} new domains checked, {len(validated_domains)} total valid so far...")
                
            try:
                # Test products.json endpoint (most reliable test for Shopify)
                test_url = f"https://{domain}/products.json"
                response = session.head(test_url, timeout=5)  # Reduced timeout for speed
                
                if response.status_code in [200, 301, 302]:
                    validated_domains.append(domain)
                    _cache_domain_result(domain, True, response.status_code)  # Cache success
                    stream_progress_update(f"   ✅ *{domain}* - ACCESSIBLE")  # Stream validated domains in italics
                else:
                    _cache_domain_result(domain, False, response.status_code)  # Cache failure
                    filtered_domains['not_accessible'].append((domain, response.status_code))
                    # Only print failures for first few to avoid spam
                    if len(filtered_domains['not_accessible']) <= 3:
                        print(f"   ❌ {i+1}: {domain} - NOT ACCESSIBLE ({response.status_code})")
                
            except requests.exceptions.ConnectionError as e:
                _cache_domain_result(domain, False, error=str(e))  # Cache failure
                filtered_domains['connection_failed'].append((domain, str(e)))
                if len(filtered_domains['connection_failed']) <= 3:
                    print(f"   ❌ {i+1}: {domain} - CONNECTION FAILED")
            except requests.exceptions.Timeout as e:
                _cache_domain_result(domain, False, error=str(e))  # Cache failure
                filtered_domains['timeout'].append((domain, str(e)))
                if len(filtered_domains['timeout']) <= 3:
                    print(f"   ⏰ {i+1}: {domain} - TIMEOUT")
            except Exception as e:
                _cache_domain_result(domain, False, error=str(e))  # Cache failure
                filtered_domains['other_errors'].append((domain, str(e)))
                if len(filtered_domains['other_errors']) <= 3:
                    print(f"   ❌ {i+1}: {domain} - ERROR")
            
            # Faster rate limiting
            time.sleep(0.1)  # Reduced from 0.2
        
        # Save cache after validation
        _save_domain_cache()
        
        # Summarized filtering report
        newly_validated = len(validated_domains) - len(cached_valid)
        total_filtered = sum(len(filtered_list) for filtered_list in filtered_domains.values())
        print(f"📊 Validation complete: {len(validated_domains)} total valid ({len(cached_valid)} cached + {newly_validated} newly validated), {total_filtered} filtered out")
        
        if validated_domains:
            # Show only newly validated domains to avoid spam
            newly_validated_domains = [d for d in validated_domains if d not in cached_valid]
            if newly_validated_domains:
                stream_progress_update(f"🎉 **Newly validated stores:** {', '.join([f'*{domain}*' for domain in newly_validated_domains])}")
        
        return validated_domains[:max_results]

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