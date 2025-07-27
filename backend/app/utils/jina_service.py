"""
Jina Reader + LLM Service
Uses Jina Reader to get clean Markdown from Shopify stores,
then uses LLM to extract structured product data
"""

import os
import requests
import json
from typing import List, Dict, Any, Optional
import time
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class JinaScrapingService:
    def __init__(self, jina_api_key: str = None, gemini_api_key: str = None):
        self.jina_api_key = jina_api_key or os.getenv("JINA_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        # Jina Reader endpoint
        self.jina_base_url = "https://r.jina.ai/"
        
        # Set up Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def scrape_products(self, store_url: str, keyword: str, max_products: int = 10) -> List[Dict[str, Any]]:
        """
        Main method: scrape products from a Shopify store using Jina Reader + LLM
        """
        print(f"   📄 Scraping {store_url} with Jina Reader...")
        
        try:
            # Step 1: Get clean markdown from Jina Reader
            markdown_content = self._get_jina_content(store_url)
            
            if not markdown_content:
                print("   ❌ No content from Jina Reader")
                return []
            
            # Step 2: Extract products using LLM
            products = self._extract_products_with_llm(markdown_content, keyword, max_products)
            
            print(f"   ✅ Extracted {len(products)} products")
            return products
            
        except Exception as e:
            print(f"   ❌ Scraping failed: {e}")
            return []
    
    def _get_jina_content(self, url: str) -> str:
        """Get clean markdown content from Jina Reader"""
        try:
            # Jina Reader URL format
            jina_url = f"{self.jina_base_url}{url}"
            
            headers = {}
            if self.jina_api_key:
                headers["Authorization"] = f"Bearer {self.jina_api_key}"
            
            response = requests.get(jina_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"   Jina Reader error {response.status_code}: {response.text}")
                return ""
                
        except Exception as e:
            print(f"   Jina Reader request failed: {e}")
            return ""
    
    def _extract_products_with_llm(self, markdown_content: str, keyword: str, max_products: int) -> List[Dict[str, Any]]:
        """Extract structured product data from markdown using LLM"""
        
        # Truncate content if too long (LLM context limits)
        max_content_length = 8000  # Leave room for prompt
        if len(markdown_content) > max_content_length:
            markdown_content = markdown_content[:max_content_length] + "..."
        
        # Create extraction prompt
        prompt = self._create_extraction_prompt(markdown_content, keyword, max_products)
        
        try:
            # Use Gemini Flash for fast, cost-effective extraction
            if not hasattr(self, 'model'):
                print("   ❌ Gemini not configured")
                return []
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2000,
                )
            )
            
            # Extract text from response, handling complex responses
            llm_output = ""
            try:
                llm_output = response.text.strip()
            except ValueError as e:
                print(f"   ⚠️ Complex response detected, extracting from parts: {str(e)}")
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            llm_output = ''.join(text_parts).strip()
                            print(f"   ✓ Extracted text from {len(text_parts)} parts")
            
            # Extract JSON from response
            products = self._parse_llm_response(llm_output)
            
            return products
            
        except Exception as e:
            print(f"   LLM extraction failed: {e}")
            return []
    
    def _create_extraction_prompt(self, content: str, keyword: str, max_products: int) -> str:
        """Create the LLM prompt for product extraction"""
        
        prompt = f"""You are a product data extraction expert. Extract structured product information from e-commerce page content. Always return valid JSON.

Extract product information from this e-commerce page content. Focus on products related to "{keyword}".

Return a JSON array of products with this exact structure:
[
  {{
    "title": "Product name",
    "price": "Display price (e.g., '$29.99')",
    "price_value": 29.99,
    "url": "Product URL (if available)",
    "image_url": "Product image URL (if available)",
    "description": "Brief product description",
    "in_stock": true,
    "sizes": ["S", "M", "L"]
  }}
]

Requirements:
- Extract up to {max_products} products maximum
- Only include products that match or relate to "{keyword}"
- Convert prices to numeric values for price_value field
- Set in_stock to true unless clearly marked as out of stock
- Include product URLs if they're relative paths (start with /)
- Return empty array [] if no relevant products found
- Return ONLY the JSON array, no other text

E-commerce page content:
{content}
"""
        return prompt
    
    def _parse_llm_response(self, llm_output: str) -> List[Dict[str, Any]]:
        """Parse and validate LLM response"""
        try:
            # Try to find JSON in the response
            import re
            
            # Look for JSON array pattern
            json_match = re.search(r'\[.*\]', llm_output, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                products = json.loads(json_str)
                
                # Validate and clean up products
                cleaned_products = []
                for product in products:
                    if isinstance(product, dict) and 'title' in product:
                        # Ensure required fields exist
                        cleaned_product = {
                            'title': product.get('title', 'Unknown Product'),
                            'price': product.get('price', 'Price not available'),
                            'price_value': float(product.get('price_value', 0.0)),
                            'url': product.get('url', ''),
                            'image_url': product.get('image_url', ''),
                            'description': product.get('description', ''),
                            'in_stock': product.get('in_stock', True),
                            'sizes': product.get('sizes', [])
                        }
                        cleaned_products.append(cleaned_product)
                
                return cleaned_products
            else:
                print("   No JSON found in LLM response")
                return []
                
        except json.JSONDecodeError as e:
            print(f"   JSON parsing failed: {e}")
            return []
        except Exception as e:
            print(f"   Response parsing failed: {e}")
            return []
    
    def test_extraction(self, test_url: str = "https://shop.gymshark.com/collections/all") -> Dict[str, Any]:
        """Test the Jina + LLM extraction pipeline"""
        print(f"🧪 Testing Jina + LLM extraction on: {test_url}")
        
        start_time = time.time()
        
        # Step 1: Test Jina Reader
        print("Step 1: Testing Jina Reader...")
        markdown = self._get_jina_content(test_url)
        jina_time = time.time() - start_time
        
        if not markdown:
            return {
                'success': False,
                'error': 'Jina Reader failed',
                'jina_time': jina_time
            }
        
        # Step 2: Test LLM extraction
        print("Step 2: Testing LLM extraction...")
        llm_start = time.time()
        products = self._extract_products_with_llm(markdown[:5000], "athletic wear", 5)
        llm_time = time.time() - llm_start
        
        total_time = time.time() - start_time
        
        return {
            'success': len(products) > 0,
            'products_found': len(products),
            'sample_product': products[0] if products else None,
            'content_length': len(markdown),
            'jina_time': jina_time,
            'llm_time': llm_time,
            'total_time': total_time,
            'products': products
        }


# Convenience functions
def scrape_store_products(store_url: str, keyword: str) -> List[Dict[str, Any]]:
    """Convenience function to scrape products from a store"""
    try:
        service = JinaScrapingService()
        return service.scrape_products(store_url, keyword)
    except Exception as e:
        print(f"Scraping failed: {e}")
        return [] 