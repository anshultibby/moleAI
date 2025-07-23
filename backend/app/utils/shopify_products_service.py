"""Simple service for fetching products from Shopify stores"""

import json
from typing import List, Dict, Any
import requests
from dataclasses import dataclass

@dataclass
class ShopifyProduct:
    """Represents a Shopify product"""
    id: str
    title: str
    description: str
    price: float
    image_url: str
    product_url: str
    store_domain: str
    variants: List[Dict[str, Any]]

class ShopifyProductsService:
    """Service for fetching products from Shopify stores"""
    
    def fetch_products(self, domain: str, limit: int = 50) -> List[ShopifyProduct]:
        """
        Fetch products from a Shopify store's products.json endpoint
        Returns list of structured product objects
        """
        print(f"\n🔍 Fetching products from {domain} (limit: {limit})")
        try:
            # Fetch products from the store
            url = f"https://{domain}/products.json?limit={limit}"
            print(f"📡 GET {url}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            products = []
            print(f"📦 Got {len(data.get('products', []))} raw products")
            
            for product in data.get('products', []):
                try:
                    # Get the main product image if available
                    image_url = ""
                    if product.get('images'):
                        image = product['images'][0]
                        image_url = image.get('src', '')
                    
                    # Get the price from the first variant
                    price = 0.0
                    if product.get('variants'):
                        variant = product['variants'][0]
                        try:
                            price = float(variant.get('price', 0))
                        except:
                            pass
                    
                    # Create product URL
                    handle = product.get('handle', '')
                    product_url = f"https://{domain}/products/{handle}" if handle else ""
                    
                    # Create structured product object
                    products.append(ShopifyProduct(
                        id=str(product.get('id', '')),
                        title=product.get('title', ''),
                        description=product.get('body_html', ''),
                        price=price,
                        image_url=image_url,
                        product_url=product_url,
                        store_domain=domain,
                        variants=product.get('variants', [])
                    ))
                except Exception as e:
                    print(f"❌ Error processing product: {e}")
                    continue
            
            print(f"✓ Processed {len(products)} products successfully")
            return products
            
        except Exception as e:
            print(f"❌ Error fetching products from {domain}: {e}")
            return []
    
    def search_products(self, domain: str, query: str = "", limit: int = 50) -> List[ShopifyProduct]:
        """
        Search for products in a store matching a query
        Basic implementation - just fetches all and filters
        """
        print(f"\n🔍 Searching products in {domain} for '{query}'")
        # Fetch more products to search through
        products = self.fetch_products(domain, limit=250)
        
        if not query:
            return products[:limit]
            
        # Better search - look for query terms in title and description
        # and handle variations of words
        query_terms = query.lower().split()
        filtered_products = []
        
        # Common word variations
        variations = {
            'coat': ['coat', 'coats', 'jacket', 'jackets', 'outerwear'],
            'dress': ['dress', 'dresses', 'gown', 'gowns'],
            'black': ['black', 'noir', 'onyx'],
            'elegant': ['elegant', 'sophisticated', 'luxury', 'luxurious', 'formal']
        }
        
        # Expand query terms with variations
        expanded_terms = []
        for term in query_terms:
            expanded_terms.append(term)
            # Add variations if they exist
            for key, values in variations.items():
                if term in values:
                    expanded_terms.extend(values)
        expanded_terms = list(set(expanded_terms))  # Remove duplicates
        
        print(f"🔍 Searching for terms: {expanded_terms}")
        
        for product in products:
            text = f"{product.title} {product.description}".lower()
            
            # Count how many terms match
            matches = sum(1 for term in expanded_terms if term in text)
            if matches > 0:
                # Add tuple of (product, matches) for sorting
                filtered_products.append((product, matches))
        
        # Sort by number of matches (descending) and extract just the products
        filtered_products.sort(key=lambda x: x[1], reverse=True)
        result = [p[0] for p in filtered_products]
        
        print(f"✓ Found {len(result)} products matching expanded terms")
        return result[:limit] 