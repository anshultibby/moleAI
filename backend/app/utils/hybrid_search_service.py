"""
Simplified Hybrid Search Service
Primary: Shopify JSON (fast, free, comprehensive)
Optional: Amazon Business via Rye (if connected)
Fallback: Jina scraping (rare cases)
"""

import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass

from .google_discovery_service import GoogleDiscoveryService
from .shopify_json_service import ShopifyJSONService, search_multiple_stores
from .jina_service import JinaScrapingService
from .rye_service import RyeAPIService


@dataclass
class SearchResult:
    products: List[Dict[str, Any]]
    total_stores_searched: int
    sources_used: Dict[str, int]
    search_time: float


class HybridSearchService:
    """Simplified: Shopify JSON-first → Amazon via Rye (optional) → Jina fallback"""
    
    def __init__(self):
        self.discovery = GoogleDiscoveryService()
        self.shopify_json = ShopifyJSONService()
        self.jina_service = JinaScrapingService()
        
        # Rye only for Amazon Business (optional)
        try:
            self.rye_service = RyeAPIService()
            self.has_rye = True
        except:
            self.rye_service = None
            self.has_rye = False
    
    async def search(self, query: str, max_results: int = 100, include_amazon: bool = True, product_callback=None) -> SearchResult:
        """
        Simplified multi-source search
        
        Args:
            query: Search query
            max_results: Maximum results to return
            include_amazon: Whether to include Amazon Business via Rye (if available)
            
        Returns:
            SearchResult with products and metadata
        """
        import time
        start_time = time.time()
        
        print(f"🔍 Starting simplified hybrid search: '{query}'")
        
        all_products = []
        sources_used = {}
        stores_searched = 0
        
        # Phase 1: Shopify JSON Search (Primary - Fast & Free)
        print("⚡ Phase 1: Shopify stores via JSON...")
        stores = self.discovery.discover_shopify_stores(query, max_results=50)  # INCREASED: More stores for better coverage
        
        if stores:
            print(f"🏪 Found {len(stores)} Shopify stores")
            shopify_products = search_multiple_stores(stores, query, max_results * 2, product_callback)  # Pass callback for streaming
            all_products.extend(shopify_products)
            sources_used['shopify_json'] = len(shopify_products)
            stores_searched = len(stores)
            print(f"   ✅ Got {len(shopify_products)} products from Shopify")
            
            # Log store diversity
            unique_stores = set(p.get('store_name', 'Unknown') for p in shopify_products)
            print(f"   🏪 Products from {len(unique_stores)} different stores")
        else:
            print("   ⚠️  No Shopify stores discovered")
        
        # Phase 2: Amazon Business via Rye (Optional)
        if include_amazon and self.has_rye and len(all_products) < max_results:
            print("🛒 Phase 2: Amazon Business via Rye...")
            
            try:
                amazon_products = self.rye_service.search_amazon_products(
                    query, 
                    limit=min(10, max_results - len(all_products))
                )
                
                if amazon_products:
                    all_products.extend(amazon_products)
                    sources_used['amazon_rye'] = len(amazon_products)
                    print(f"   ✅ Got {len(amazon_products)} products from Amazon")
                else:
                    print("   ⚠️  No Amazon Business products (may need setup)")
                    
            except Exception as e:
                print(f"   ❌ Amazon search failed: {e}")
        
        # Phase 3: Jina fallback for stubborn stores (Rare)
        if len(all_products) < max_results // 3:
            print("🛡️  Phase 3: Jina fallback for missing results...")
            
            if stores:
                # Find stores that didn't return JSON results
                stores_with_results = {self._normalize_store_name(p.get('store_name', '')) for p in all_products if 'shopify' in p.get('source', '')}
                empty_stores = [s for s in stores[:3] if self._normalize_store_name(s) not in stores_with_results]
                
                if empty_stores:
                    jina_products = await self._jina_search_stores(empty_stores, query, max_results - len(all_products))
                    all_products.extend(jina_products)
                    sources_used['jina_scrape'] = len(jina_products)
                    print(f"   ✅ Got {len(jina_products)} products from Jina fallback")
        
        # Phase 4: Final ranking and deduplication (LLM filtering already done in batches)
        print(f"📊 Phase 4: Final ranking and deduplication of {len(all_products)} products...")
        
        # Deduplicate and rank - LLM filtering was already done in 200-product batches
        final_products = self._rank_and_dedupe(all_products, query)
        print(f"   ✅ Final deduplication: {len(all_products)} → {len(final_products)} unique products")
        
        # Products were already streamed during batch LLM filtering, no need to stream again
        
        # Only limit if we have way more than needed
        if len(final_products) > max_results * 1.5:
            final_products = final_products[:max_results]
        
        search_time = time.time() - start_time
        print(f"✅ Search completed in {search_time:.2f}s - {len(final_products)} products")
        
        return SearchResult(
            products=final_products,
            total_stores_searched=stores_searched,
            sources_used=sources_used,
            search_time=search_time
        )
    
    async def search_shopify_only(self, query: str, max_results: int = 100, product_callback=None) -> SearchResult:
        """
        Pure Shopify search - fastest and most reliable
        """
        import time
        start_time = time.time()
        
        print(f"🏪 Pure Shopify search: '{query}'")
        
        # Discover and search Shopify stores
        stores = self.discovery.discover_shopify_stores(query, max_results=50)  # Get more stores
        
        if stores:
            # search_multiple_stores now does LLM filtering in 200-product batches
            products = search_multiple_stores(stores, query, max_results * 2, product_callback)  # Pass callback for streaming
            
            # LLM filtering is already done in batches during search - no need for additional filtering
            print(f"✅ Got {len(products)} LLM-filtered products from Shopify stores")
                
            sources_used = {'shopify_json': len(products)}
        else:
            products = []
            sources_used = {}
        
        search_time = time.time() - start_time
        print(f"✅ Shopify-only search: {len(products)} products in {search_time:.2f}s")
        
        return SearchResult(
            products=products,
            total_stores_searched=len(stores) if stores else 0,
            sources_used=sources_used,
            search_time=search_time
        )

    async def _jina_search_stores(self, stores: List[str], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Use Jina scraping for stores that didn't have JSON results"""
        products = []
        
        for store in stores[:2]:  # Limit to 2 stores for speed
            try:
                print(f"   🔍 Jina scraping {store}...")
                store_products = self.jina_service.scrape_products(
                    f"https://{store}/collections/all", 
                    query, 
                    max_products=3
                )
                products.extend(store_products)
                
                if len(products) >= max_results:
                    break
                    
            except Exception as e:
                print(f"   ❌ Jina error for {store}: {e}")
                continue
        
        return products
    
    def _rank_and_dedupe(self, products: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Remove duplicates and rank by relevance"""
        # Remove duplicates based on product name similarity
        unique_products = []
        seen_names = set()
        
        for product in products:
            name = product.get('product_name', '').lower().strip()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_products.append(product)
        
        # Rank by relevance score (already calculated) or title match
        query_words = query.lower().split()
        
        def relevance_score(product):
            score = product.get('relevance_score', 0)
            if score == 0:  # Calculate if not already done
                title = product.get('product_name', '').lower()
                for word in query_words:
                    if word in title:
                        score += 2
            return score
        
        return sorted(unique_products, key=relevance_score, reverse=True)
    
    def _normalize_store_name(self, store_domain: str) -> str:
        """Normalize store domain to comparable name"""
        domain = store_domain.lower().replace('https://', '').replace('http://', '')
        if '.myshopify.com' in domain:
            return domain.split('.myshopify.com')[0].replace('-', ' ')
        return domain.split('.')[0]


# Simple wrapper function for easy integration
async def hybrid_search(query: str, max_results: int = 20, product_callback=None) -> List[Dict[str, Any]]:
    """
    Main search function - Shopify JSON-first with optional Amazon
    
    Args:
        query: Search query
        max_results: Max products to return
        product_callback: Optional callback to stream products as they're found
        
    Returns:
        List of product dictionaries
    """
    service = HybridSearchService()
    result = await service.search(query, max_results, include_amazon=True, product_callback=product_callback)
    return result.products


# Pure Shopify search function
async def shopify_search(query: str, max_results: int = 100, product_callback=None) -> List[Dict[str, Any]]:
    """
    Pure Shopify search - fastest option
    
    Args:
        query: Search query
        max_results: Max products to return (increased default)
        product_callback: Optional callback to stream products as they're found
        
    Returns:
        List of product dictionaries  
    """
    service = HybridSearchService()
    result = await service.search_shopify_only(query, max_results, product_callback)
    return result.products 