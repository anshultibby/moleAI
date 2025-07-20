"""
Rye API Service
Handles product search using Rye's GraphQL API for Amazon, Walmart, Target and Shopify products
"""

import os
import requests
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class RyeAPIService:
    def __init__(self, api_key: str = None, shopper_ip: str = None):
        self.api_key = api_key or os.getenv("RYE_API_KEY")
        self.shopper_ip = shopper_ip or os.getenv("RYE_SHOPPER_IP", "127.0.0.1")
        # Use production endpoint for better product availability
        self.base_url = "https://graphql.api.rye.com/v1/query"
        
        if not self.api_key:
            raise ValueError("RYE_API_KEY not found in environment variables")
        
        # Use Basic auth format as specified in Rye docs
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Rye-Shopper-IP": self.shopper_ip,
            "Content-Type": "application/json"
        }

    def search_enhanced_products(self, query: str, include_amazon: bool = True, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Enhanced search combining Shopify stores + Amazon Business (if available)
        """
        all_products = []
        
        # Search Shopify stores (existing working method)
        print(f"🔍 Enhanced search for '{query}'...")
        shopify_products = self.search_products_by_query(query, ["SHOPIFY"], limit // 2)
        all_products.extend(shopify_products)
        
        # Try Amazon Business if enabled and available
        if include_amazon:
            try:
                amazon_products = self.search_amazon_products(query, limit // 2)
                all_products.extend(amazon_products)
            except Exception as e:
                print(f"Amazon search skipped: {e}")
        
        # Remove duplicates and rank
        unique_products = self._deduplicate_products(all_products)
        ranked_products = self._rank_products_by_relevance(unique_products, query)
        
        print(f"🎯 Enhanced search complete: {len(ranked_products)} total products")
        return ranked_products[:limit]
    
    def _deduplicate_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate products based on title similarity"""
        unique_products = []
        seen_titles = set()
        
        for product in products:
            # Normalize title for comparison
            title = product.get('product_name', '').lower().strip()
            title_key = ''.join(title.split())  # Remove spaces for better matching
            
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_products.append(product)
        
        return unique_products
    
    # Comprehensive list of working Shopify domains across different categories
    # This is our "product database" until Rye provides a global search API
    def get_shopify_domains(self) -> List[str]:
        """
        Returns a comprehensive list of Shopify domains that work with Rye.
        This is dynamically expandable as we discover more working stores.
        """
        return [
            # Athletic & Fitness
            "shop.gymshark.com",
            "us.allbirds.com", 
            "shop.bombas.com",
            
            # Fashion & Apparel (examples - would need to test these)
            # "shop.patagonia.com",
            # "shop.nike.com", 
            # "adidas.com",
            # "levi.com",
            # "uniqlo.com",
            
            # Beauty & Personal Care
            # "shop.glossier.com",
            # "fenty.com",
            
            # Home & Lifestyle
            # "shop.westelm.com",
            # "cb2.com",
            
            # Tech & Electronics
            # "store.google.com",
            # "apple.com",
            
            # Food & Beverage
            # "shop.bluebottle.com",
            # "shop.sweetgreen.com",
            
            # Add more domains as we verify they work with Rye
        ]
    
    def search_products_by_domain(self, domain: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for products within a specific domain using productsByDomainV2
        """
        # Use the exact working query format from our test
        query = f"""
        query {{
            productsByDomainV2(input: {{domain: "{domain}"}}, pagination: {{limit: {limit}, offset: 0}}) {{
                id
                title
                description
                price {{
                    value
                    currency
                    displayValue
                }}
                images {{
                    url
                }}
                url
                isAvailable
                marketplace
            }}
        }}
        """
        
        # No variables needed with inline format
        variables = None
        
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
                
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"GraphQL Error for {domain}: {data['errors'][0]['message']}")
                    return []
                
                products = data.get("data", {}).get("productsByDomainV2", [])
                return self._transform_products(products)
            else:
                print(f"HTTP Error {response.status_code} for {domain}")
                return []
                
        except Exception as e:
            print(f"Error fetching products from {domain}: {str(e)}")
            return []
    
    def search_products_by_query(self, query: str, marketplaces: List[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Enhanced search across ALL available Shopify stores with intelligent filtering
        """
        if marketplaces is None:
            marketplaces = ["SHOPIFY"]
        
        working_domains = self.get_shopify_domains()
        all_products = []
        
        # Calculate products per domain to get variety
        products_per_domain = max(10, limit // len(working_domains) + 5)
        
        print(f"🔍 Searching {len(working_domains)} stores for '{query}'")
        
        # Search all domains in parallel (simulate with sequential for now)
        for domain in working_domains:
            try:
                print(f"   🏪 Searching {domain}...")
                domain_products = self.search_products_by_domain(domain, limit=products_per_domain)
                
                # Enhanced filtering with intelligent text matching
                filtered_products = self._filter_products_by_query(domain_products, query)
                
                all_products.extend(filtered_products)
                print(f"   ✅ Found {len(filtered_products)} matching products")
                
            except Exception as e:
                print(f"   ❌ Error searching {domain}: {str(e)}")
                continue
        
        # Sort by relevance and return top results
        all_products = self._rank_products_by_relevance(all_products, query)
        
        print(f"🎯 Total products found: {len(all_products)}, returning top {min(limit, len(all_products))}")
        return all_products[:limit]
    
    def _filter_products_by_query(self, products: List[Dict], query: str) -> List[Dict]:
        """
        Intelligent product filtering with advanced text matching
        """
        if not query:
            return products
        
        query_terms = query.lower().split()
        filtered_products = []
        
        for product in products:
            # Create comprehensive searchable text
            searchable_content = " ".join([
                product.get('product_name', ''),
                product.get('description', ''),
                product.get('store_name', ''),
                # Add more fields for better matching
            ]).lower()
            
            # Calculate match score using multiple criteria
            exact_matches = sum(1 for term in query_terms if term in searchable_content)
            partial_matches = sum(1 for term in query_terms 
                                if any(term in word for word in searchable_content.split()))
            
            # Score products based on matches
            total_score = exact_matches * 2 + partial_matches
            
            if total_score > 0:
                product['relevance_score'] = total_score
                product['match_ratio'] = total_score / len(query_terms)
                filtered_products.append(product)
        
        return filtered_products
    
    def _rank_products_by_relevance(self, products: List[Dict], query: str) -> List[Dict]:
        """
        Advanced ranking algorithm for search results
        """
        # Sort by multiple criteria:
        # 1. Relevance score (primary)
        # 2. Product availability
        # 3. Price (secondary consideration)
        
        def ranking_key(product):
            relevance = product.get('relevance_score', 0)
            availability = 1 if product.get('is_available', True) else 0
            # Boost popular/well-known brands
            brand_boost = 1.2 if any(brand in product.get('store_name', '').lower() 
                                   for brand in ['gymshark', 'allbirds', 'bombas']) else 1.0
            
            return relevance * availability * brand_boost
        
        return sorted(products, key=ranking_key, reverse=True)
    
    def _transform_products(self, products: List[Dict]) -> List[Dict[str, Any]]:
        """
        Transform Rye API product format to our standard format
        """
        transformed = []
        for product in products:
            try:
                # Since we don't have store info in the simplified query, 
                # derive store name from marketplace and URL
                marketplace = product.get('marketplace', 'SHOPIFY')
                product_url = product.get('url', '')
                
                # Try to extract store name from URL
                store_name = 'Unknown Store'
                if product_url:
                    try:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(product_url)
                        domain = parsed_url.netloc
                        
                        # Map known domains to friendly names
                        domain_map = {
                            'shop.gymshark.com': 'Gymshark',
                            'us.allbirds.com': 'Allbirds', 
                            'shop.bombas.com': 'Bombas'
                        }
                        store_name = domain_map.get(domain, domain.replace('shop.', '').replace('us.', '').replace('.com', '').title())
                    except:
                        store_name = f'{marketplace} Store'
                
                transformed_product = {
                    'id': product.get('id'),
                    'product_name': product.get('title', 'Unknown Product'),
                    'description': product.get('description', ''),
                    'price': product.get('price', {}).get('displayValue', 'Price not available'),
                    'price_value': float(product.get('price', {}).get('value', 0)),
                    'currency': product.get('price', {}).get('currency', 'USD'),
                    'image_url': product.get('images', [{}])[0].get('url', '') if product.get('images') else '',
                    'product_url': product_url,
                    'store_name': store_name,
                    'marketplace': marketplace,
                    'is_available': product.get('isAvailable', True),
                    'type': 'product'
                }
                transformed.append(transformed_product)
            except Exception as e:
                print(f"Error transforming product: {e}")
                continue
        
        return transformed

    def search_products(self, query: str, max_price: float = None, category: str = None, 
                       marketplaces: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Main search method that matches the expected interface from gemini_tools_converter
        """
        if marketplaces is None:
            marketplaces = ["SHOPIFY"]  # Focus on what works reliably
        
        # Use the enhanced query-based search
        products = self.search_products_by_query(query, marketplaces, limit)
        
        # Apply price filter if specified
        if max_price:
            products = [p for p in products if p.get('price_value', float('inf')) <= max_price]
        
        return products
    
    def search_amazon_products(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search Amazon Business products via Rye API
        Note: This requires having Amazon Business connected to your Rye account
        """
        print(f"🏪 Searching Amazon Business for '{query}'...")
        
        # Rye doesn't have a direct Amazon search - we need to use domain-based search
        # or work with pre-requested Amazon products
        try:
            # Try searching Amazon domain if connected
            amazon_products = self.search_products_by_domain("amazon.com", limit)
            
            # Filter by query
            if amazon_products:
                filtered = self._filter_products_by_query(amazon_products, query)
                print(f"   ✅ Found {len(filtered)} Amazon products")
                return filtered
            else:
                print(f"   ⚠️  No Amazon Business integration or products found")
                return []
                
        except Exception as e:
            print(f"   ❌ Amazon search error: {e}")
            return []
    
    def search_by_product_url(self, url: str, marketplace: str = "AMAZON") -> Optional[Dict[str, Any]]:
        """
        Add a specific product by URL (Amazon or Shopify)
        This is the main way to add individual products to Rye
        """
        query = f"""
        mutation {{
            requestProductByURL(input: {{
                url: "{url}",
                marketplace: {marketplace}
            }}) {{
                productID
            }}
        }}
        """
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query},
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code == 200 and "data" in result:
                product_id = result["data"]["requestProductByURL"]["productID"]
                print(f"✅ Added {marketplace} product: {product_id}")
                
                # Now fetch the product details
                return self.get_product_by_id(product_id, marketplace)
            else:
                print(f"❌ Failed to add product: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error adding product: {e}")
            return None

    def get_product_by_id(self, product_id: str, marketplace: str) -> Optional[Dict[str, Any]]:
        """Get detailed product information by ID"""
        query = f"""
        query {{
            productByID(input: {{
                id: "{product_id}",
                marketplace: "{marketplace}"
            }}) {{
                id
                title
                description
                price {{
                    value
                    currency
                    displayValue
                }}
                images {{
                    url
                }}
                url
                isAvailable
                marketplace
            }}
        }}
        """
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query},
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code == 200 and "data" in result:
                product = result["data"]["productByID"]
                return self._transform_product_data_simple(product)
            else:
                print(f"Failed to get product {product_id}: {result}")
                return None
                
        except Exception as e:
            print(f"Error getting product {product_id}: {e}")
            return None

    def _transform_product_data_simple(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform simple product data from productByID query"""
        try:
            return {
                'id': product.get('id'),
                'product_name': product.get('title', 'Unknown Product'),
                'description': product.get('description', ''),
                'price': product.get('price', {}).get('displayValue', 'Price not available'),
                'price_value': float(product.get('price', {}).get('value', 0)),
                'currency': product.get('price', {}).get('currency', 'USD'),
                'image_url': product.get('images', [{}])[0].get('url', '') if product.get('images') else '',
                'product_url': product.get('url', ''),
                'store_name': 'Amazon Business' if product.get('marketplace') == 'AMAZON' else 'Shopify Store',
                'marketplace': product.get('marketplace', 'UNKNOWN'),
                'is_available': product.get('isAvailable', True),
                'source': f'rye_{product.get("marketplace", "unknown").lower()}',
                'type': 'product'
            }
        except Exception as e:
            print(f"Error transforming product: {e}")
            return None
    
    def add_working_domain(self, domain: str) -> bool:
        """
        Test and add a new domain to our working list if it has products
        """
        test_products = self.search_products_by_domain(domain, limit=5)
        if test_products:
            print(f"✅ {domain} is working with {len(test_products)} products")
            # In a real implementation, you'd save this to a database
            return True
        else:
            print(f"❌ {domain} has no accessible products")
            return False 

    def _transform_product_data(self, product_data: Dict[str, Any], marketplace_source: str) -> Optional[Dict[str, Any]]:
        """
        Transform product data from different marketplace structures to our standard format
        """
        try:
            # Extract basic product info
            title = product_data.get('title', 'Unknown Product')
            description = product_data.get('description', '')
            vendor = product_data.get('vendor', '')
            
            # Extract image
            images = product_data.get('images', {}).get('edges', [])
            image_url = images[0]['node']['url'] if images else ''
            
            # Extract price from first variant
            variants = product_data.get('variants', {}).get('edges', [])
            if not variants:
                return None
                
            variant = variants[0]['node']
            price_info = variant.get('price', {})
            price_amount = price_info.get('amount', '0')
            currency = price_info.get('currencyCode', 'USD')
            
            # Format price display
            price_display = f"${float(price_amount):.2f}" if currency == 'USD' else f"{float(price_amount):.2f} {currency}"
            
            # Extract store info
            store_info = product_data.get('store', {})
            store_name = store_info.get('name', marketplace_source.title())
            store_url = store_info.get('url', '')
            
            # Build product URL (this would need marketplace-specific logic)
            product_url = store_url  # Simplified for now
            
            return {
                'id': product_data.get('id'),
                'product_name': title,
                'description': description,
                'price': price_display,
                'price_value': float(price_amount) if price_amount else 0.0,
                'currency': currency,
                'image_url': image_url,
                'product_url': product_url,
                'store_name': store_name,
                'marketplace': marketplace_source.upper(),
                'is_available': variant.get('availableForSale', True),
                'vendor': vendor,
                'source': f'rye_{marketplace_source}',
                'type': 'product'
            }
            
        except Exception as e:
            print(f"   ⚠️  Error transforming {marketplace_source} product: {e}")
            return None 