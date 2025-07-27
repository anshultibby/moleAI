"""
LLM-based Product Filter
Handles intelligent filtering of products using language models

ENHANCED CRITERIA-MATCHING PIPELINE:
┌─────────────────────────────────────────────────────────────────┐
│ RAW DATA: limit * 10 per store (e.g. 30 * 10 = 300 products)   │
│          ↓                                                      │
│ REASONABLE CATEGORY: Remove obvious mismatches only             │
│          ↓                                                      │
│ RANDOMIZATION: Shuffle for diversity                            │
│          ↓                                                      │
│ SMART PREFILTER: 100 max → Score-based selection               │
│          ↓                                                      │
│ FINAL RANDOMIZATION: Shuffle again                              │
│          ↓                                                      │
│ LLM INPUT: Up to 100 products                                   │
│          ↓                                                      │
│ ENHANCED LLM FILTERING: Accurate gender + criteria matching    │
│          ↓                                                      │
│ PRECISE MATCHES: 5-15 products with accurate criteria          │
└─────────────────────────────────────────────────────────────────┘

BALANCED MATCHING APPROACH:
🎯 CORE REQUIREMENTS (Must have):
- Product Type/Category (jacket, jeans, shoes)
- Basic relevance to query

✅ EXPLICIT CRITERIA (Strongly preferred):
- Color Requirements (black, red, blue)  
- Material Requirements (cotton, leather, denim)
- Size Requirements (large, XL, size 8)
- Brand Requirements (Nike, Apple, etc.)

⚖️ FLEXIBLE CRITERIA (Nice to have):
- Style/Fit Requirements (skinny, oversized)
- Price Preferences (cheap, premium)
- Function/Use Hints (running, work, casual)
- Gender/Age Hints (men's, women's)

BALANCED RULE:
- Core requirements: MUST match
- Explicit criteria: STRONGLY preferred (high score bonus)
- Flexible criteria: Nice to have (small score bonus)
- Result: 15-30 good matches from multiple domains instead of 8-20 products
"""

import os
from typing import List, Dict, Any
import random
from ..debug_tracker import get_debug_tracker
from ..funnel_visualizer import get_funnel_visualizer


class LLMProductFilter:
    """Handles LLM-based filtering of products for relevance and attribute matching"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
    def filter_products(self, products: List[Dict], query: str) -> List[Dict]:
        """Use LLM to filter products for relevance - OPTIMIZED for diversity and volume"""
        if not products or not query.strip():
            return products
        
        original_count = len(products)
        debug_tracker = get_debug_tracker()
        
        if debug_tracker:
            debug_tracker.start_timing_phase("llm_filter")
        
        # STEP 1: REMOVED STRICT CATEGORY PREFILTERING - let LLM handle it
        print(f"   🚀 Skipping strict prefiltering - sending all {len(products)} products to LLM")
        
        # STEP 2: RANDOMIZE EARLY - before any scoring/prefiltering to avoid order bias
        random.shuffle(products)
        
        # STEP 3: REMOVED prefiltering limit - let more products through
        # Keep the smart prefiltering for relevance scoring but don't limit count
        if len(products) > 300:  # Only prefilter if we have a very large number
            products = self._smart_prefilter_products(products, query, max_products=len(products))  # No limit
            print(f"   🎯 Pre-filtered: kept most relevant {len(products)} products")
        
        # STEP 4: FINAL RANDOMIZE - critical for LLM diversity
        shuffled_products = products.copy()
        random.shuffle(shuffled_products)
        
        # STEP 5: REMOVED INPUT LIMIT - let LLM see all filtered products
        products = shuffled_products
        print(f"   🔀 Using all {len(products)} products for LLM processing")
        
        if not self.api_key:
            print("   ⚠️  No Gemini API key, using basic filtering")
            return self._basic_filter_by_query(products, query)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Create compact product list for LLM
            product_list = self._create_llm_product_list(products)
            
            # ENHANCED STRICT FILTERING: Zero tolerance for irrelevant results
            prompt = f"""ULTRA-STRICT FILTER for: "{query}"

{chr(10).join(product_list)}

🚨 CRITICAL STRICT MATCHING RULES - USER TRUST DEPENDS ON ACCURACY:

❌ IMMEDIATE REJECTION CRITERIA:
- Wrong product category (if user asks for "shoes", don't include anything that isn't shoes)
- Wrong gender (if "men's" is specified, zero women's items allowed)
- Wrong material (if "leather" specified, no fabric/cotton items)
- Wrong color (if "black" specified, no blue/red/other colors unless it's genuinely black)
- Wrong size category (if "large" specified, no small/medium items)

✅ MANDATORY REQUIREMENTS:
1. **EXACT PRODUCT TYPE MATCH**: Query must match the CORE product category
   - "jacket" = ONLY jackets (no coats, blazers, sweaters unless explicitly jacket-like)
   - "dress" = ONLY dresses (no skirts, tops, rompers)
   - "headphones" = ONLY headphones (no earbuds unless specifically mentioned)
   - "laptop" = ONLY laptops (no tablets, phones, accessories)

2. **GENDER PRECISION**: If gender specified, ZERO tolerance for wrong gender
   - "men's" = ABSOLUTELY NO women's items (even if unisex)
   - "women's" = ABSOLUTELY NO men's items (even if unisex)
   - "kids" = ABSOLUTELY NO adult items

3. **COLOR ACCURACY**: If color specified, must be that exact color or very close shade
   - "black" = only black, very dark gray, charcoal
   - "white" = only white, off-white, cream
   - "red" = only red, burgundy, crimson (no pink, orange)

4. **MATERIAL PRECISION**: If material specified, must contain that material
   - "leather" = must be genuine or faux leather (no fabric)
   - "cotton" = must contain cotton (not polyester, wool, etc.)
   - "denim" = must be denim material

5. **SIZE REQUIREMENTS**: If size mentioned, must have that size available
   - Only include if the specific size is clearly available

🎯 TRUST-BUILDING APPROACH:
- Better to show 3-5 PERFECT matches than 15 mediocre ones
- Users prefer fewer, highly relevant results over many irrelevant ones
- If query is very specific, be extra strict on ALL criteria
- Only include products you're confident the user would actually want

⚠️ ZERO TOLERANCE POLICY:
Reject any product that doesn't meet ALL specified criteria. User trust is more important than quantity.

Return ONLY the numbers of products that PERFECTLY match all user requirements (aim for 3-8 highly relevant products):"""

            response = model.generate_content(prompt)
            
            # Extract text from response, handling complex responses
            response_text = ""
            if response:
                try:
                    response_text = response.text
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
                                response_text = ''.join(text_parts)
                                print(f"   ✓ Extracted text from {len(text_parts)} parts")
            
            if response_text:
                try:
                    # Parse numbers from LLM response
                    import re
                    numbers = re.findall(r'\b\d+\b', response_text.strip())
                    relevant_indices = [int(n) - 1 for n in numbers if 0 <= int(n) - 1 < len(products)]
                    
                    filtered_products = [products[i] for i in relevant_indices]
                    
                    print(f"   🤖 LLM: {len(products)} → {len(filtered_products)} selected")
                    
                    # Add relevance scores based on LLM order
                    for idx, product in enumerate(filtered_products):
                        product['relevance_score'] = len(filtered_products) - idx + 100
                    
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
    
    def _create_llm_product_list(self, products: List[Dict]) -> List[str]:
        """Create simplified product list for LLM processing - LEAN & FAST"""
        product_list = []
        
        for i, product in enumerate(products):
            # MINIMAL: Just name and type - no complex processing
            name = product.get('product_name', '').strip()
            product_type = product.get('product_type', '').strip()
            
            # Simple format: number and name
            product_summary = f"{i+1}. {name}"
            
            # Add type only if different from name and useful
            if product_type and product_type.lower() not in name.lower():
                product_summary += f" ({product_type})"
            
            product_list.append(product_summary)
        
        return product_list
    
    def _smart_prefilter_products(self, products: List[Dict], query: str, max_products: int = 100) -> List[Dict]:
        """Smart but GENEROUS pre-filtering to get diverse candidates for LLM processing"""
        query_words = [word.lower() for word in query.split() if len(word) >= 2]
        if not query_words:
            # If no query words, randomize for diversity
            random.shuffle(products)
            return products[:max_products] if max_products < len(products) else products
        
        # If max_products is same as input length, just score and return all
        if max_products >= len(products):
            # Score all products but return them all
            scored_products = []
            for product in products:
                score = self._score_product_relevance(product, query_words)
                scored_products.append((score, product))
            
            # Sort by score but return all
            scored_products.sort(key=lambda x: x[0], reverse=True)
            result = [product for score, product in scored_products]
            print(f"   📊 Scored all {len(result)} products by relevance (no filtering needed)")
            return result
        
        # Score products based on query relevance - MORE GENEROUS SCORING
        scored_products = []
        
        for product in products:
            score = self._score_product_relevance(product, query_words)
            scored_products.append((score, product))
        
        # Sort by score and return candidates - MUCH MORE GENEROUS
        scored_products.sort(key=lambda x: x[0], reverse=True)
        
        # DIVERSITY-FIRST: Include products with minimal relevance AND randomize within score tiers
        filtered_products = []
        
        # Tier 1: High relevance (score > 8) - take most but not all
        high_score = [product for score, product in scored_products if score > 8]
        if high_score:
            random.shuffle(high_score)  # Randomize within tier
            filtered_products.extend(high_score[:max_products // 2])  # Take half from high scores
        
        # Tier 2: Medium relevance (score 3-8) - take some
        medium_score = [product for score, product in scored_products if 3 <= score <= 8]
        if medium_score:
            random.shuffle(medium_score)  # Randomize within tier
            remaining_slots = max_products - len(filtered_products)
            filtered_products.extend(medium_score[:remaining_slots // 2])
        
        # Tier 3: Low relevance (score 1-2) - take a few for serendipity
        low_score = [product for score, product in scored_products if 1 <= score <= 2]
        if low_score and len(filtered_products) < max_products:
            random.shuffle(low_score)  # Randomize
            remaining_slots = max_products - len(filtered_products)
            filtered_products.extend(low_score[:min(remaining_slots, max_products // 10)])  # Take 10% from low scores
        
        # Fill remaining slots with any products if we're short
        if len(filtered_products) < max_products:
            used_products = set(id(p) for p in filtered_products)
            remaining_products = [product for score, product in scored_products if id(product) not in used_products]
            random.shuffle(remaining_products)
            remaining_slots = max_products - len(filtered_products)
            filtered_products.extend(remaining_products[:remaining_slots])
        
        print(f"   📊 Generous + Diverse pre-filtering: {len(products)} → {len(filtered_products)} candidates")
        print(f"   🎲 Randomized within score tiers for maximum diversity")
        
        return filtered_products[:max_products]
    
    def _score_product_relevance(self, product: Dict, query_words: List[str]) -> int:
        """Score a single product's relevance to query words"""
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
        
        return score
    
    def _basic_filter_by_query(self, products: List[Dict], query: str) -> List[Dict]:
        """BASIC filtering - let LLM handle complex matching"""
        if not query.strip():
            return products
        
        # Parse query for requirements
        query_lower = query.lower()
        query_words = [word.strip() for word in query_lower.split() if len(word.strip()) >= 2]
        
        # STEP 1: REMOVED strict category filtering - let LLM handle it
        print(f"   🚀 Basic filter: sending all {len(products)} products (no prefiltering)")
        
        # STEP 2: Extract REQUIRED criteria from query - BE MORE PRECISE
        colors = ['black', 'white', 'red', 'blue', 'navy', 'green', 'yellow', 'pink', 'purple', 'brown', 'gray', 'grey', 'beige', 'tan', 'orange']
        materials = ['cotton', 'wool', 'silk', 'denim', 'leather', 'polyester', 'linen', 'cashmere']
        sizes = ['xs', 'small', 'medium', 'large', 'xl', 'extra large', 'xxl']  # Removed 's', 'm', 'l' to avoid false matches
        brands = ['nike', 'adidas', 'apple', 'samsung', 'sony', 'zara', 'h&m']
        genders = ['men', 'mens', "men's", 'women', 'womens', "women's", 'kids', 'baby']
        
        # Find REQUIRED criteria in query - use word boundaries for sizes
        required_colors = [color for color in colors if color in query_lower]
        required_materials = [material for material in materials if material in query_lower]
        # For sizes, check for whole words or common patterns like 'size l', 'size m'
        required_sizes = []
        for size in sizes:
            if f' {size} ' in f' {query_lower} ' or f'size {size}' in query_lower or query_lower.endswith(f' {size}'):
                required_sizes.append(size)
        required_brands = [brand for brand in brands if brand in query_lower]
        required_genders = [gender for gender in genders if gender in query_lower]
        
        print(f"   🔍 Basic filtering - REQUIRED criteria:")
        print(f"      Colors: {required_colors}")
        print(f"      Materials: {required_materials}")
        print(f"      Sizes: {required_sizes}")
        print(f"      Brands: {required_brands}")
        print(f"      Genders: {required_genders}")
        
        # LOOSE BASIC FILTERING: Let LLM handle the strict matching
        total_requirements = len(required_colors + required_materials + required_sizes + required_brands + required_genders)
        
        # If no specific requirements, return all products (let LLM handle strict filtering)
        if total_requirements == 0:
            print(f"   ✅ No specific requirements found - returning all {len(products)} products for strict LLM filtering")
            return products
        
        # Only apply basic filtering for very specific multi-requirement queries
        if total_requirements <= 2:  # Allow up to 2 specific requirements before basic filtering
            print(f"   ✅ Minimal requirements ({total_requirements}) - returning all {len(products)} products for strict LLM filtering")
            return products
        
        # Only apply basic filtering for very specific queries (3+ requirements)
        print(f"   🔍 Found multiple specific requirements ({total_requirements}) - applying basic filtering")
        strict_products = []
        
        for product in products:
            # Get searchable text
            name = product.get('product_name', '').lower()
            product_type = product.get('product_type', '').lower()
            tags = ' '.join(product.get('tags', [])).lower()
            description = product.get('description', '').lower()
            vendor = product.get('vendor', '').lower()
            
            searchable_text = f"{name} {product_type} {tags} {description} {vendor}"
            
            # STRICT REQUIREMENTS - ALL must be satisfied
            meets_requirements = True
            rejection_reason = ""
            
            # Check colors - MUST have if specified
            if required_colors:
                has_required_color = any(color in searchable_text for color in required_colors)
                if not has_required_color:
                    meets_requirements = False
                    rejection_reason = f"missing required colors: {required_colors}"
            
            # Check materials - MUST have if specified
            if required_materials and meets_requirements:
                has_required_material = any(material in searchable_text for material in required_materials)
                if not has_required_material:
                    meets_requirements = False
                    rejection_reason = f"missing required materials: {required_materials}"
            
            # Check sizes - MUST have if specified
            if required_sizes and meets_requirements:
                has_required_size = any(size in searchable_text for size in required_sizes)
                if not has_required_size:
                    meets_requirements = False
                    rejection_reason = f"missing required sizes: {required_sizes}"
            
            # Check brands - MUST have if specified
            if required_brands and meets_requirements:
                has_required_brand = any(brand in searchable_text for brand in required_brands)
                if not has_required_brand:
                    meets_requirements = False
                    rejection_reason = f"missing required brands: {required_brands}"
            
            # Check genders - MUST have if specified
            if required_genders and meets_requirements:
                has_required_gender = any(gender in searchable_text for gender in required_genders)
                if not has_required_gender:
                    meets_requirements = False
                    rejection_reason = f"missing required genders: {required_genders}"
            
            # Core relevance: must match main query words - BE MORE LENIENT
            if meets_requirements:
                matched_words = sum(1 for word in query_words if word in searchable_text)
                # Much more lenient - only require 1 word match for long queries, or any partial relevance
                min_matches = 1 if len(query_words) > 2 else max(1, len(query_words) // 2)
                if matched_words < min_matches:
                    meets_requirements = False
                    rejection_reason = f"insufficient keyword matches: {matched_words}/{len(query_words)} (need {min_matches})"
            
            if meets_requirements:
                strict_products.append(product)
                print(f"   ✅ ACCEPT: {product.get('product_name', 'Unknown')[:40]}...")
            else:
                print(f"   ❌ REJECT: {product.get('product_name', 'Unknown')[:40]}... ({rejection_reason})")
        
        print(f"   📊 STRICT basic filtering: {len(products)} → {len(strict_products)} products (only exact matches)")
        return strict_products
    
    def _apply_basic_keyword_filtering(self, products: List[Dict], query_words: List[str]) -> List[Dict]:
        """Apply basic keyword filtering even when no specific requirements found"""
        if not query_words:
            return products
            
        filtered_products = []
        
        for product in products:
            # Get searchable text
            name = product.get('product_name', '').lower()
            product_type = product.get('product_type', '').lower()
            tags = ' '.join(product.get('tags', [])).lower()
            description = product.get('description', '').lower()
            vendor = product.get('vendor', '').lower()
            
            searchable_text = f"{name} {product_type} {tags} {description} {vendor}"
            
            # STRICT: Require at least 75% of query words to match
            matched_words = sum(1 for word in query_words if word in searchable_text)
            match_ratio = matched_words / len(query_words) if query_words else 0
            
            # Much stricter threshold: require 75% word match for most queries
            min_ratio = 0.75 if len(query_words) > 1 else 1.0  # Single word must match exactly
            
            if match_ratio >= min_ratio:
                filtered_products.append(product)
            else:
                print(f"   ❌ REJECT: {product.get('product_name', 'Unknown')[:40]}... (only {matched_words}/{len(query_words)} words matched)")
        
        print(f"   📊 Basic keyword filtering: {len(products)} → {len(filtered_products)} products (≥75% word match)")
        return filtered_products 