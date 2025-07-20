"""
Shopify JSON Service
Fast direct access to Shopify store product data via /products.json endpoints
"""

import requests
import time
import random
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin
import re


class ShopifyJSONService:
    """Direct access to Shopify store product feeds via /products.json"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache'
        })
    
    def search_store_products(self, store_domain: str, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search products in a Shopify store using /products.json
        
        Args:
            store_domain: Store domain (e.g., 'gymshark.com' or 'shop.gymshark.com')
            query: Search query
            limit: Max products to return
            
        Returns:
            List of product dictionaries filtered by LLM for relevance
        """
        # Validate domain before processing
        if not self._is_valid_domain(store_domain):
            print(f"❌ Skipping invalid domain: {store_domain}")
            return []
            
        try:
            # Step 1: Extract all available products (no filtering yet)
            raw_products, working_base_url = self._extract_all_available_products(store_domain, limit * 8)  # INCREASED: Get even MORE for LLM to filter
            
            if not raw_products:
                return []
            
            # Double-check that working_base_url is not localhost
            if working_base_url and not self._is_valid_domain(working_base_url):
                print(f"❌ Working base URL is invalid: {working_base_url}")
                return []
            
            # Step 2: Convert to LLM-friendly format
            llm_readable_products = self._convert_to_llm_format(raw_products, working_base_url)
            
            # Step 3: Use LLM to filter for relevance
            relevant_products = self._llm_filter_products(llm_readable_products, query)
            
            return relevant_products[:limit]
            
        except Exception as e:
            print(f"❌ Error searching {store_domain}: {e}")
            return []

    def _extract_all_available_products(self, store_domain: str, max_products: int) -> Tuple[List[Dict], str]:
        """Extract raw product data from Shopify store - no filtering, just extraction"""
        clean_domain = self._clean_domain(store_domain)
        all_products = []
        working_base_url = ""
        
        # Try multiple URL patterns
        for base_url in self._get_url_variants(clean_domain):
            try:
                store_products = self._fetch_raw_products_from_url(base_url, max_products)
                if store_products:  # If we got results, save the working URL
                    all_products.extend(store_products)
                    working_base_url = base_url
                    break
            except Exception:
                continue  # Try next URL variant
        
        return all_products, working_base_url

    def _fetch_raw_products_from_url(self, base_url: str, limit: int) -> List[Dict]:
        """Fetch raw products from a specific Shopify URL - minimal processing"""
        products = []
        page = 1
        
        while len(products) < limit and page <= 3:  # Max 3 pages
            url = f"{base_url}/products.json"
            params = {
                'limit': min(250, limit),  # Shopify max is 250
                'page': page,
                'published_status': 'published'  # Only get published products
            }
            
            print(f"   📄 Fetching {url} (page {page})")
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            page_products = data.get('products', [])
            
            if not page_products:
                break  # No more products
            
            # Filter for valid, accessible products
            for product in page_products:
                if self._is_valid_product(product):
                    products.append(product)
            
            page += 1
            time.sleep(0.5)  # Be polite
        
        return products

    def _is_valid_product(self, product: Dict) -> bool:
        """
        Check if a product is valid and will have working links
        """
        # Check required fields
        if not product.get('title') or not product.get('handle'):
            return False
        
        # Check if product has variants and is available
        variants = product.get('variants', [])
        if not variants:
            return False
        
        # Check if at least one variant is available
        has_available_variant = any(v.get('available', False) for v in variants)
        if not has_available_variant:
            return False
        
        # Check published status (some stores include unpublished products)
        published_at = product.get('published_at')
        if not published_at or published_at == 'null':
            return False
        
        # Check handle is valid (no empty or invalid characters)
        handle = product.get('handle', '')
        if not handle or len(handle) < 2 or any(char in handle for char in [' ', '&', '?', '#']):
            return False
        
        # Check if product has basic required data
        if not product.get('images') and not product.get('body_html'):
            # Product has no images and no description - likely incomplete
            return False
        
        return True

    def _convert_to_llm_format(self, raw_products: List[Dict], store_url: str) -> List[Dict[str, Any]]:
        """Convert raw Shopify products to clean, LLM-readable format"""
        llm_products = []
        
        for product in raw_products:
            try:
                # Extract essential data for LLM analysis
                variants = product.get('variants', [])
                if not variants:
                    continue
                
                first_variant = variants[0]
                
                # Get first image with proper URL handling
                images = product.get('images', [])
                image_url = ""
                if images:
                    raw_image_url = images[0].get('src', '') if isinstance(images[0], dict) else str(images[0])
                    image_url = self._fix_image_url(raw_image_url, store_url)
                
                # Build clean product data for LLM
                llm_product = {
                    'product_name': product.get('title', '').strip(),
                    'price': self._format_price(first_variant.get('price', '0')),
                    'price_value': self._parse_price_value(first_variant.get('price', '0')),
                    'description': self._clean_html(product.get('body_html', ''))[:200],  # Truncate for LLM
                    'product_type': product.get('product_type', '').strip(),
                    'vendor': product.get('vendor', '').strip(),
                    'tags': [tag.strip() for tag in product.get('tags', []) if tag.strip()],
                    'handle': product.get('handle', ''),
                    
                    # For final output - validate URLs
                    'image_url': image_url,
                    'product_url': self._build_validated_product_url(store_url, product.get('handle', '')),
                    'store_name': self._extract_store_name(store_url),
                    'store_url': store_url,
                    'availability': 'in stock',
                    'source': 'shopify_json'
                }
                
                llm_products.append(llm_product)
                
            except Exception as e:
                print(f"   ⚠️  Error converting product: {e}")
                continue
        
        return llm_products
    
    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize domain"""
        domain = domain.lower().strip()
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.rstrip('/')
        return domain
    
    def _get_url_variants(self, domain: str) -> List[str]:
        """Generate possible Shopify URL variants"""
        variants = []
        
        # Direct domain
        if not domain.endswith('.myshopify.com'):
            variants.append(f"https://{domain}")
        
        # MyShopify subdomain
        if '.myshopify.com' in domain:
            variants.append(f"https://{domain}")
        else:
            # Extract store name and try myshopify.com
            store_name = domain.split('.')[0]
            variants.append(f"https://{store_name}.myshopify.com")
        
        return variants
    
    def _llm_filter_products(self, products: List[Dict], query: str) -> List[Dict]:
        """Use LLM to filter products for relevance - much more accurate than rules"""
        if not products or not query.strip():
            return products
        
        # INCREASED: Don't limit to just 15 - we want to find more relevant products
        original_count = len(products)
        
        # Pre-filter products to get better candidates for LLM - MUCH MORE GENEROUS
        if len(products) > 100:  # Only pre-filter if we have lots of products
            products = self._smart_prefilter_products(products, query, max_products=100)  # INCREASED: More candidates
            print(f"   🎯 Pre-filtered: {original_count} → {len(products)} products (kept most relevant)")
        
        # Shuffle products to ensure variety and avoid bias toward first products
        import random
        if len(products) > 75:  # INCREASED: LLM can handle more now
            shuffled_products = products.copy()
            random.shuffle(shuffled_products)
            products = shuffled_products[:75]  # INCREASED: Send more to LLM
            print(f"   🔀 Shuffled and selected 75 products for LLM processing (from {len(shuffled_products)} candidates)")
        elif len(products) > 10:
            # Still shuffle smaller lists for variety
            shuffled_products = products.copy()
            random.shuffle(shuffled_products)
            products = shuffled_products
            print(f"   🔀 Shuffled {len(products)} products for variety")
        
        try:
            import google.generativeai as genai
            import os
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("   ⚠️  No Gemini API key, using basic filtering")
                return self._basic_filter_by_query(products, query)
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Create compact product list for LLM - SIMPLIFIED
            product_list = []
            for i, product in enumerate(products):
                # Only include the MOST RELEVANT fields for LLM filtering
                name = product.get('product_name', '').strip()
                product_type = product.get('product_type', '').strip()
                tags = product.get('tags', [])[:4]  # Top 4 tags only
                
                # Create a SIMPLE, focused description for the LLM
                product_summary = f"{i+1}. {name}"
                
                # Add type if it's different from name and adds value
                if product_type and product_type.lower() not in name.lower():
                    product_summary += f" ({product_type})"
                
                # Add key tags that aren't already in name/type
                relevant_tags = []
                name_lower = name.lower()
                type_lower = product_type.lower()
                
                for tag in tags:
                    tag_clean = tag.strip().lower()
                    if (tag_clean and 
                        len(tag_clean) > 2 and 
                        tag_clean not in name_lower and 
                        tag_clean not in type_lower and
                        len(relevant_tags) < 3):  # Max 3 additional tags
                        relevant_tags.append(tag.strip())
                
                if relevant_tags:
                    product_summary += f" [{', '.join(relevant_tags)}]"
                
                product_list.append(product_summary)
            
            prompt = f"""Filter products for: "{query}"

Products to evaluate:
{chr(10).join(product_list)}

STRICT MATCHING RULES:
• COLOR: If query specifies color (black, white, red, etc.), product MUST have that exact color
• MATERIAL: If query specifies material (cotton, wool, silk, etc.), product MUST have that material  
• STYLE: If query specifies style (dress, jeans, leggings, etc.), product MUST be that exact style
• FIT: If query specifies fit (skinny, high-waisted, etc.), product MUST have that fit

REJECT if ANY specified attribute is missing or doesn't match.

Examples:
"black leggings" → ONLY black leggings (not dark blue, not pants)
"cotton dress" → ONLY cotton dresses (not polyester, not tops)  
"skinny jeans" → ONLY skinny jeans (not regular, not leggings)

Return ONLY the numbers of matching products (e.g., "2, 7, 15"):"""

            response = model.generate_content(prompt)
            
            if response and response.text:
                try:
                    # Parse numbers from LLM response
                    import re
                    numbers = re.findall(r'\b\d+\b', response.text.strip())
                    relevant_indices = [int(n) - 1 for n in numbers if 0 <= int(n) - 1 < len(products)]
                    
                    filtered_products = [products[i] for i in relevant_indices]
                    
                    print(f"   🤖 LLM: {len(products)} → {len(filtered_products)} relevant products")
                    
                    # Add relevance scores based on LLM order
                    for idx, product in enumerate(filtered_products):
                        product['relevance_score'] = len(filtered_products) - idx + 100  # Higher score for LLM picks
                    
                    return filtered_products
                    
                except Exception as e:
                    print(f"   ⚠️  LLM response parsing error: {e}")
                    return self._basic_filter_by_query(products, query)
            else:
                print(f"   ⚠️  Empty LLM response")
                return self._basic_filter_by_query(products, query)
                
        except Exception as e:
            print(f"   ⚠️  LLM filtering failed: {e}")
            return self._basic_filter_by_query(products, query)

    def _smart_prefilter_products(self, products: List[Dict], query: str, max_products: int = 100) -> List[Dict]:
        """Smart but GENEROUS pre-filtering to get good candidates for LLM processing"""
        query_words = [word.lower() for word in query.split() if len(word) >= 2]  # Reduced minimum length
        if not query_words:
            return products[:max_products]
        
        # Score products based on query relevance - MORE GENEROUS SCORING
        scored_products = []
        
        for product in products:
            score = 0
            
            # Get searchable text
            name = product.get('product_name', '').lower()
            product_type = product.get('product_type', '').lower()
            tags = ' '.join(product.get('tags', [])).lower()
            vendor = product.get('vendor', '').lower()
            description = product.get('description', '').lower()
            
            searchable_text = f"{name} {product_type} {tags} {vendor} {description}"
            
            # GENEROUS scoring - give points for any matches
            for word in query_words:
                # Higher score for matches in product name
                if word in name:
                    score += 10
                # Medium score for matches in type or tags
                if word in product_type:
                    score += 6
                if word in tags:
                    score += 5
                # Lower score for matches in description or vendor
                if word in description:
                    score += 3
                if word in vendor:
                    score += 2
                
                # GENEROUS: Also give partial credit for substring matches
                if len(word) >= 4:  # Only for longer words to avoid too much noise
                    if any(word in token for token in searchable_text.split()):
                        score += 1
            
            # Bonus for having multiple query words - MORE GENEROUS
            matched_words = sum(1 for word in query_words if word in searchable_text)
            if matched_words >= 2:
                score += matched_words * 4  # Increased bonus
            elif matched_words == 1:
                score += 2  # Still give some bonus for one match
            
            # REDUCED penalty for short names (was -2, now -1)
            if len(name) < 8:  # Reduced threshold and penalty
                score -= 1
            
            # NEW: Bonus for products with detailed info
            if len(description) > 50:
                score += 1
            if len(tags) > 3:
                score += 1
            
            scored_products.append((score, product))
        
        # Sort by score and return candidates - MUCH MORE GENEROUS
        scored_products.sort(key=lambda x: x[0], reverse=True)
        
        # GENEROUS: Include products with even minimal relevance (score > 0)
        # Instead of requiring high scores, let LLM decide
        filtered_products = []
        for score, product in scored_products:
            if score > 0:  # Very low threshold - let LLM decide quality
                filtered_products.append(product)
            elif len(filtered_products) < max_products // 2:  # Fill at least half quota
                filtered_products.append(product)  # Include even low-scoring ones if we need more
        
        # If we still don't have enough, add more regardless of score
        if len(filtered_products) < max_products:
            remaining_products = [product for score, product in scored_products[len(filtered_products):]]
            filtered_products.extend(remaining_products[:max_products - len(filtered_products)])
        
        print(f"   📊 Generous pre-filtering: {len(products)} → {len(filtered_products)} candidates (score range: {scored_products[0][0] if scored_products else 0} to {scored_products[-1][0] if scored_products else 0})")
        
        return filtered_products[:max_products]

    def _basic_filter_by_query(self, products: List[Dict], query: str) -> List[Dict]:
        """Enhanced basic keyword-based filtering with strict attribute matching"""
        if not query.strip():
            return products
        
        # Parse query for specific attributes
        query_lower = query.lower()
        query_words = [word.strip() for word in query_lower.split() if len(word.strip()) >= 2]
        
        # Extract specific attributes from query
        colors = ['black', 'white', 'red', 'blue', 'navy', 'green', 'yellow', 'pink', 'purple', 'brown', 'gray', 'grey', 'beige', 'tan', 'orange']
        materials = ['cotton', 'wool', 'silk', 'denim', 'leather', 'polyester', 'nylon', 'spandex', 'cashmere', 'linen', 'velvet', 'suede']
        styles = ['dress', 'shirt', 'pants', 'jeans', 'leggings', 'shorts', 'skirt', 'jacket', 'coat', 'sweater', 'hoodie', 'tank', 'blouse', 'cardigan']
        fits = ['skinny', 'slim', 'regular', 'loose', 'oversized', 'fitted', 'relaxed', 'straight', 'wide', 'cropped', 'high-waisted', 'low-rise']
        
        # Find required attributes in query
        required_colors = [color for color in colors if color in query_lower]
        required_materials = [material for material in materials if material in query_lower]
        required_styles = [style for style in styles if style in query_lower]
        required_fits = [fit for fit in fits if fit.replace('-', ' ') in query_lower or fit.replace('-', '') in query_lower]
        
        print(f"   🔍 Attribute filtering - Colors: {required_colors}, Materials: {required_materials}, Styles: {required_styles}, Fits: {required_fits}")
        
        filtered_products = []
        
        for product in products:
            # Get searchable text
            name = product.get('product_name', '').lower()
            product_type = product.get('product_type', '').lower()
            tags = ' '.join(product.get('tags', [])).lower()
            description = product.get('description', '').lower()
            vendor = product.get('vendor', '').lower()
            
            searchable_text = f"{name} {product_type} {tags} {description} {vendor}"
            
            # Check if ALL required attributes are present
            matches_all_attributes = True
            
            # Check required colors
            for required_color in required_colors:
                if required_color not in searchable_text:
                    matches_all_attributes = False
                    print(f"   ❌ {product.get('product_name', 'Unknown')[:30]}... - Missing color: {required_color}")
                    break
            
            if not matches_all_attributes:
                continue
                
            # Check required materials
            for required_material in required_materials:
                if required_material not in searchable_text:
                    matches_all_attributes = False
                    print(f"   ❌ {product.get('product_name', 'Unknown')[:30]}... - Missing material: {required_material}")
                    break
            
            if not matches_all_attributes:
                continue
                
            # Check required styles
            for required_style in required_styles:
                if required_style not in searchable_text:
                    matches_all_attributes = False
                    print(f"   ❌ {product.get('product_name', 'Unknown')[:30]}... - Missing style: {required_style}")
                    break
            
            if not matches_all_attributes:
                continue
                
            # Check required fits  
            for required_fit in required_fits:
                fit_variants = [required_fit, required_fit.replace('-', ' '), required_fit.replace('-', '')]
                if not any(variant in searchable_text for variant in fit_variants):
                    matches_all_attributes = False
                    print(f"   ❌ {product.get('product_name', 'Unknown')[:30]}... - Missing fit: {required_fit}")
                    break
            
            if matches_all_attributes:
                # Additional basic keyword matching for other terms
                basic_match_score = 0
                for word in query_words:
                    if word not in colors + materials + styles + [fit.replace('-', '') for fit in fits]:
                        if word in searchable_text:
                            basic_match_score += 1
                
                # Only include if it has good basic keyword matching too
                if basic_match_score > 0 or len(required_colors + required_materials + required_styles + required_fits) > 0:
                    print(f"   ✅ {product.get('product_name', 'Unknown')[:50]}... - Matches all attributes")
                    filtered_products.append(product)
        
        print(f"   📊 Strict attribute filtering: {len(products)} → {len(filtered_products)} products")
        return filtered_products

    def _filter_by_query(self, products: List[Dict], query: str) -> List[Dict]:
        """Main filtering method - uses LLM for best results, falls back to basic filtering"""
        # First, do basic availability and quality filtering
        available_products = [p for p in products if p.get('availability') == 'in stock']
        
        if not available_products:
            return []
        
        # Then use LLM for relevance filtering
        return self._llm_filter_products(available_products, query)
    
    def _format_price(self, price: str) -> str:
        """Format price consistently"""
        try:
            price_float = float(price)
            return f"${price_float:.2f}"
        except:
            return str(price)

    def _parse_price_value(self, price_str: str) -> float:
        """Parse price string to float value for filtering"""
        try:
            # Remove currency symbols and commas, handle various formats
            import re
            # Extract numeric value from price string
            price_match = re.search(r'[\d,]+\.?\d*', str(price_str))
            if price_match:
                cleaned_price = price_match.group().replace(',', '')
                return float(cleaned_price)
            return 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def _clean_html(self, html_text: str) -> str:
        """Clean HTML from description"""
        if not html_text:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        # Clean up whitespace
        clean_text = ' '.join(clean_text.split())
        # Truncate to reasonable length
        return clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
    
    def _extract_store_name(self, store_url: str) -> str:
        """Extract clean store name from URL with better fallback handling"""
        if not store_url:
            return "Unknown Store"
            
        try:
            domain = store_url.replace('https://', '').replace('http://', '').rstrip('/')
            
            # Handle myshopify.com domains
            if '.myshopify.com' in domain:
                store_name = domain.split('.myshopify.com')[0]
                # Clean up store name
                store_name = store_name.replace('-', ' ').replace('_', ' ')
                # Capitalize properly
                return ' '.join(word.capitalize() for word in store_name.split())
            
            # Handle custom domains
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                # Try to get the brand name (second to last part)
                brand_part = domain_parts[-2]
                
                # Skip common subdomains
                if brand_part in ['www', 'shop', 'store', 'buy']:
                    if len(domain_parts) >= 3:
                        brand_part = domain_parts[-3]
                
                # Clean and format the brand name
                brand_part = brand_part.replace('-', ' ').replace('_', ' ')
                return ' '.join(word.capitalize() for word in brand_part.split())
            
            # Fallback: use the whole domain but clean it up
            clean_domain = domain.replace('.com', '').replace('.co', '').replace('.net', '')
            clean_domain = clean_domain.replace('-', ' ').replace('_', ' ')
            return ' '.join(word.capitalize() for word in clean_domain.split())
            
        except Exception as e:
            print(f"   ⚠️  Error extracting store name from '{store_url}': {e}")
            return "Store"  # Generic fallback

    def _fix_image_url(self, image_url: str, store_url: str) -> str:
        """Fix and validate image URLs to ensure they're accessible"""
        if not image_url:
            return ""
        
        try:
            # Handle protocol-relative URLs (starting with //)
            if image_url.startswith('//'):
                image_url = f"https:{image_url}"
            
            # Handle relative URLs (starting with /)
            elif image_url.startswith('/'):
                base_domain = store_url.rstrip('/')
                image_url = f"{base_domain}{image_url}"
            
            # Handle URLs that are already absolute
            elif image_url.startswith(('http://', 'https://')):
                pass  # Already good
            
            # Handle Shopify CDN URLs that might be missing protocol
            elif 'cdn.shopify.com' in image_url:
                if not image_url.startswith(('http://', 'https://')):
                    image_url = f"https://{image_url}"
            
            # Ensure high quality image (remove size restrictions)
            if 'cdn.shopify.com' in image_url:
                # Remove size parameters to get full resolution
                image_url = re.sub(r'_\d+x\d*\.', '.', image_url)
                image_url = re.sub(r'_\d+x\.', '.', image_url)
                image_url = re.sub(r'_x\d+\.', '.', image_url)
            
            return image_url
            
        except Exception as e:
            print(f"   ⚠️  Error fixing image URL '{image_url}': {e}")
            return image_url  # Return original if fixing fails

    def _is_valid_domain(self, domain: str) -> bool:
        """Check if domain is valid for Shopify search (not localhost, not fake domains)"""
        if not domain:
            return False
        
        domain = domain.lower().strip()
        
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.rstrip('/')
        
        # Filter out localhost and development domains
        localhost_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            'localhost:',  # Catches localhost:3000, localhost:8080, etc.
        ]
        
        for pattern in localhost_patterns:
            if pattern in domain:
                print(f"   🚫 Filtering out localhost domain: {domain}")
                return False
        
        # Filter out fake/test domains
        fake_domains = [
            'example.com',
            'test.com',
            'sample.com',
            'demo.com',
            'fake.com'
        ]
        
        for fake in fake_domains:
            if fake in domain:
                print(f"   🚫 Filtering out fake domain: {domain}")
                return False
        
        # Must have at least one dot for valid domain
        if '.' not in domain:
            return False
        
        return True

    def _build_validated_product_url(self, store_url: str, handle: str) -> str:
        """Build a validated product URL from store URL and handle."""
        if not store_url or not handle:
            return ""
        
        try:
            base_url = store_url.rstrip('/')
            product_url = f"{base_url}/products/{handle}"
            
            # Basic URL validation - check for common issues but be less strict
            # Allow special characters that are common in product names (™, ®, etc.)
            handle_clean = handle.replace('-', '').replace('_', '').replace('™', '').replace('®', '')
            if not handle_clean.replace('with', '').replace('and', '').isalnum() and len(handle_clean) > 0:
                # Only warn for truly suspicious handles, not common product naming
                suspicious_chars = ['<', '>', '"', "'", ';', '&', '?', '#']
                if any(char in handle for char in suspicious_chars):
                    print(f"   ⚠️  Suspicious handle: {handle}")
                
            return product_url
            
        except Exception as e:
            print(f"   ⚠️  Error building product URL: {e}")
            return ""

    def _test_product_url(self, product_url: str) -> bool:
        """Test if a product URL is accessible (optional validation)"""
        if not product_url:
            return False
            
        try:
            # Quick HEAD request to check if URL exists
            response = self.session.head(product_url, timeout=3)
            return response.status_code in [200, 301, 302]
        except:
            # Don't fail products due to network issues, just warn
            return True  # Assume it's valid

    def _test_domain_accessibility(self, domain: str) -> bool:
        """Test if a domain is actually accessible before processing"""
        if not domain:
            return False
            
        # Clean domain for testing
        clean_domain = self._clean_domain(domain)
        
        # Test both the direct domain and myshopify variant
        test_urls = []
        
        # Add HTTPS version of the domain
        if not clean_domain.startswith('http'):
            test_urls.append(f"https://{clean_domain}")
        else:
            test_urls.append(clean_domain)
            
        # For non-myshopify domains, also test the myshopify variant
        if not clean_domain.endswith('.myshopify.com'):
            store_name = clean_domain.split('.')[0]
            test_urls.append(f"https://{store_name}.myshopify.com")
        
        # Test each URL variant
        for test_url in test_urls:
            try:
                # Test products.json endpoint (most reliable indicator of Shopify store)
                products_url = f"{test_url}/products.json"
                response = self.session.head(products_url, timeout=5)
                
                if response.status_code in [200, 301, 302]:
                    print(f"   ✅ Domain accessible: {test_url}")
                    return True
                    
            except (requests.exceptions.RequestException, Exception):
                continue  # Try next URL variant
        
        print(f"   ❌ Domain not accessible: {domain}")
        return False

    def _validate_and_filter_domains(self, domains: List[str]) -> List[str]:
        """Filter domains to only include accessible ones"""
        print(f"🔍 Validating {len(domains)} domains for accessibility...")
        
        valid_domains = []
        
        for domain in domains:
            # First check basic domain validity
            if not self._is_valid_domain(domain):
                continue
                
            # Then check if domain is actually accessible
            if self._test_domain_accessibility(domain):
                valid_domains.append(domain)
            
            # Rate limiting to be respectful
            import time
            time.sleep(0.2)
        
        filtered_count = len(domains) - len(valid_domains)
        if filtered_count > 0:
            print(f"🚫 Filtered out {filtered_count} inaccessible domains")
        
        print(f"✅ {len(valid_domains)} domains are accessible and valid")
        return valid_domains


def search_multiple_stores(store_domains: List[str], query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Search multiple Shopify stores and combine results
    
    Args:
        store_domains: List of store domains to search
        query: Search query
        max_results: Maximum total results to return
        
    Returns:
        Combined and ranked product list
    """
    service = ShopifyJSONService()
    all_products = []
    
    # Filter domains for validity and accessibility
    valid_domains = service._validate_and_filter_domains(store_domains)
    
    if not valid_domains:
        print("❌ No valid, accessible domains to search")
        return []
    
    results_per_store = max(10, max_results // len(valid_domains)) if valid_domains else 20  # Increased minimum per store
    
    for domain in valid_domains:
        print(f"🏪 Searching {domain}...")
        try:
            products = service.search_store_products(domain, query, results_per_store)
            all_products.extend(products)
            print(f"   ✅ Found {len(products)} products")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Remove duplicates based on product name + store
    seen = set()
    unique_products = []
    for product in all_products:
        key = (product.get('product_name', ''), product.get('store_name', ''))
        if key not in seen:
            seen.add(key)
            unique_products.append(product)
    
    # Sort by relevance score if available, otherwise by store name
    unique_products.sort(key=lambda x: (
        x.get('relevance_score', 0),
        x.get('store_name', '')
    ), reverse=True)
    
    return unique_products[:max_results] 