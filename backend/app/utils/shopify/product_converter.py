"""
Shopify Product Data Converter
Handles conversion of raw Shopify JSON to clean, structured product data
"""

from typing import List, Dict, Any, Tuple
import re
from html import unescape
from urllib.parse import urljoin, urlparse


# Import funnel tracking
try:
    from ..funnel_visualizer import get_funnel_visualizer
except ImportError:
    def get_funnel_visualizer():
        return None


class ShopifyProductConverter:
    """Converts raw Shopify product data to clean, structured format"""
    
    def convert_to_llm_format(self, raw_products: List[Dict], store_url: str) -> List[Dict[str, Any]]:
        """Convert raw Shopify products to clean, LLM-readable format"""
        llm_products = []
        funnel_visualizer = get_funnel_visualizer()
        
        for product in raw_products:
            try:
                # Extract and validate variants
                variants = product.get('variants', [])
                if not variants:
                    # Track prefilter decision
                    if funnel_visualizer:
                        funnel_visualizer.track_prefilter_decision(product, "No variants available", "removed")
                    continue  # Skip products without variants
                
                # Filter to only available variants
                available_variants = [v for v in variants if v.get('available', False)]
                if not available_variants:
                    # Track prefilter decision
                    if funnel_visualizer:
                        funnel_visualizer.track_prefilter_decision(product, "No available variants", "removed")
                    continue  # Skip products with no available variants
                
                # Get the best available variant (usually first available one)
                first_variant = available_variants[0]
                
                # Extract variant information for LLM context
                variant_info = self._extract_variant_info(available_variants, product.get('options', []))
                
                # Get first image with proper URL handling
                images = product.get('images', [])
                image_url = ""
                if images:
                    raw_image_url = images[0].get('src', '') if isinstance(images[0], dict) else str(images[0])
                    image_url = self._fix_image_url(raw_image_url, store_url)
                
                # Build clean product data for LLM
                llm_product = {
                    'product_name': product.get('title', '').strip(),
                    'price': first_variant.get('price', '0'),  # Clean numeric price
                    'price_value': self._parse_price_value(first_variant.get('price', '0')),
                    'currency': 'USD',  # Shopify prices are typically in USD unless specified
                    'description': self._clean_html(product.get('body_html', ''))[:200],  # Truncated for LLM
                    'product_type': product.get('product_type', '').strip(),
                    'vendor': product.get('vendor', '').strip(),
                    'tags': [tag.strip() for tag in product.get('tags', []) if tag.strip()],
                    'handle': product.get('handle', ''),
                    
                    # NEW: Variant information for better LLM understanding
                    'available_sizes': variant_info['sizes'],
                    'available_colors': variant_info['colors'],
                    'variant_count': len(available_variants),
                    'options': variant_info['options'],
                    
                    # For final output - validate URLs
                    'image_url': image_url,
                    'product_url': self._build_validated_product_url(store_url, product.get('handle', '')),
                    'store_name': self._extract_store_name(store_url),
                    'store_url': store_url,
                    'availability': 'in stock',  # We know it's available since we filtered
                    'source': 'shopify_json'
                }
                
                # Track successful prefilter decision
                if funnel_visualizer:
                    funnel_visualizer.track_prefilter_decision(product, "Passed variant and availability checks", "kept")
                
                llm_products.append(llm_product)
                
            except Exception as e:
                # Track error in prefiltering
                if funnel_visualizer:
                    funnel_visualizer.track_prefilter_decision(product, f"Conversion error: {str(e)}", "removed")
                print(f"   ⚠️  Error converting product: {e}")
                continue
        
        return llm_products
    
    def _extract_variant_info(self, available_variants: List[Dict], options: List[Dict]) -> Dict:
        """Extract useful variant information for LLM context"""
        variant_info = {
            'sizes': [],
            'colors': [],
            'options': []
        }
        
        try:
            # Get option names to understand what the variants represent
            option_names = [opt.get('name', '').lower() for opt in options]
            
            for variant in available_variants:
                # Extract option values (handle None values)
                option1 = (variant.get('option1') or '').strip()
                option2 = (variant.get('option2') or '').strip()
                option3 = (variant.get('option3') or '').strip()
                
                # Categorize options based on common patterns
                for i, option_name in enumerate(option_names):
                    option_value = [option1, option2, option3][i] if i < 3 else ''
                    if not option_value:
                        continue
                        
                    option_value_lower = option_value.lower()
                    
                    # Size patterns
                    size_patterns = ['size', 'sizes']
                    if any(pattern in option_name for pattern in size_patterns):
                        if option_value not in variant_info['sizes']:
                            variant_info['sizes'].append(option_value)
                    
                    # Color patterns  
                    color_patterns = ['color', 'colour', 'col']
                    if any(pattern in option_name for pattern in color_patterns):
                        if option_value not in variant_info['colors']:
                            variant_info['colors'].append(option_value)
                    
                    # General option tracking
                    option_entry = f"{option_name}: {option_value}"
                    if option_entry not in variant_info['options']:
                        variant_info['options'].append(option_entry)
            
            # Also try to detect sizes/colors from option values themselves
            for variant in available_variants:
                for option_val in [variant.get('option1'), variant.get('option2'), variant.get('option3')]:
                    if not option_val:
                        continue
                        
                    option_val = option_val.strip()
                    option_val_lower = option_val.lower()
                    
                    # Common size indicators
                    if option_val_lower in ['xs', 'xsmall', 'extra small', 's', 'small', 'm', 'medium', 'l', 'large', 'xl', 'xlarge', 'extra large', 'xxl', '2xl', 'xxxl', '3xl']:
                        if option_val not in variant_info['sizes']:
                            variant_info['sizes'].append(option_val)
                    
                    # Common color indicators
                    colors = ['black', 'white', 'red', 'blue', 'green', 'yellow', 'pink', 'purple', 'brown', 'gray', 'grey', 'navy', 'beige', 'tan', 'orange']
                    if any(color in option_val_lower for color in colors):
                        if option_val not in variant_info['colors']:
                            variant_info['colors'].append(option_val)
        
        except Exception as e:
            print(f"   ⚠️  Error extracting variant info: {e}")
        
        return variant_info
    
    def _format_price(self, price_value: str) -> str:
        """Format price value to display string"""
        try:
            # Shopify prices are already in dollars (e.g., "329.99")
            price_float = float(price_value)
            return f"${price_float:.2f}"
        except (ValueError, TypeError):
            return "Price not available"
    
    def _parse_price_value(self, price_value: str) -> float:
        """Parse price value to float for comparisons"""
        try:
            return float(price_value)  # Shopify prices are already in dollars
        except (ValueError, TypeError):
            return 0.0
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content to plain text"""
        if not html_content:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities
        clean_text = unescape(clean_text)
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def _fix_image_url(self, raw_image_url: str, store_url: str) -> str:
        """Fix relative or protocol-relative image URLs"""
        if not raw_image_url:
            return ""
        
        # Handle protocol-relative URLs
        if raw_image_url.startswith('//'):
            return f"https:{raw_image_url}"
        
        # Handle relative URLs
        if raw_image_url.startswith('/'):
            return urljoin(store_url, raw_image_url)
        
        # Return as-is if already absolute
        return raw_image_url
    
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
    
    def _extract_store_name(self, store_url: str) -> str:
        """Extract a readable store name from URL"""
        try:
            parsed = urlparse(store_url)
            domain = parsed.netloc.lower()
            
            # Extract store name from myshopify.com domains
            if '.myshopify.com' in domain:
                store_name = domain.split('.myshopify.com')[0]
                # Convert hyphens to spaces and title case
                return store_name.replace('-', ' ').title()
            
            # For custom domains, use the domain name
            return domain.replace('www.', '').replace('.com', '').title()
            
        except Exception:
            return "Unknown Store" 