"""
LLM-based Product Filter
Handles intelligent filtering of products using language models
"""

import os
from typing import List, Dict, Any
import random
from ..debug_tracker import get_debug_tracker


class LLMProductFilter:
    """Handles LLM-based filtering of products for relevance and attribute matching"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
    def filter_products(self, products: List[Dict], query: str) -> List[Dict]:
        """Use LLM to filter products for relevance - EXTREMELY AGGRESSIVE about category matching"""
        if not products or not query.strip():
            return products
        
        original_count = len(products)
        debug_tracker = get_debug_tracker()
        
        if debug_tracker:
            debug_tracker.start_timing_phase("llm_filter")
        
        # STEP 1: Pre-filter with strict category validation to catch obvious mismatches
        products = self._strict_category_prefilter(products, query)
        
        if len(products) != original_count:
            print(f"   🚫 Strict category filter: {original_count} → {len(products)} products (rejected obvious mismatches)")
            # Track prefiltering decisions
            if debug_tracker:
                rejected_count = original_count - len(products)
                for i in range(rejected_count):
                    debug_tracker.track_prefilter_decision(
                        {"title": "Category Mismatch Product", "variants": [{"price": "Unknown"}]},
                        "Failed strict category validation",
                        "removed"
                    )
        
        # STEP 2: Continue with existing logic for remaining products
        if len(products) > 100:
            products = self._smart_prefilter_products(products, query, max_products=100)
            print(f"   🎯 Pre-filtered: kept most relevant {len(products)} products")
        
        # Shuffle products to ensure variety and avoid bias toward first products
        if len(products) > 75:
            shuffled_products = products.copy()
            random.shuffle(shuffled_products)
            products = shuffled_products[:75]
            print(f"   🔀 Shuffled and selected 75 products for LLM processing")
        elif len(products) > 10:
            shuffled_products = products.copy()
            random.shuffle(shuffled_products)
            products = shuffled_products
            print(f"   🔀 Shuffled {len(products)} products for variety")
        
        if not self.api_key:
            print("   ⚠️  No Gemini API key, using basic filtering")
            return self._basic_filter_by_query(products, query)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Create compact product list for LLM
            product_list = self._create_llm_product_list(products)
            
            # ENHANCED: Much more aggressive prompt for category matching
            prompt = f"""ULTRA-STRICT Product Filter for: "{query}"

Products to evaluate:
{chr(10).join(product_list)}

🚨 ZERO TOLERANCE RULES - REJECT if ANY rule is violated:

1. CATEGORY MATCHING (CRITICAL):
   • "jacket" query → ONLY jackets, blazers, coats (NEVER jeans, pants, shirts, dresses)
   • "jeans" query → ONLY jeans, denim pants (NEVER jackets, shirts, dresses, leggings)  
   • "dress" query → ONLY dresses (NEVER tops, pants, skirts, jackets)
   • "shoes" query → ONLY shoes, boots, sneakers (NEVER clothing, accessories)
   • "bag" query → ONLY bags, purses, backpacks (NEVER clothing, shoes)

2. SPECIFIC ATTRIBUTES (if specified):
   • COLOR: Must have exact color (black ≠ dark blue ≠ charcoal)
   • MATERIAL: Must have exact material (cotton ≠ polyester ≠ blend)
   • STYLE: Must match style exactly (skinny ≠ regular ≠ wide)
   • FIT: Must match fit exactly (high-waisted ≠ low-rise)

3. FUNCTION/USE CASE:
   • Different product categories serve different functions
   • A jacket cannot substitute for jeans, ever
   • A dress cannot substitute for pants, ever

EXAMPLES OF STRICT FILTERING:
• "black jacket" → REJECT all jeans, even black jeans (wrong category)
• "winter coat" → REJECT all sweaters, hoodies (wrong function) 
• "running shoes" → REJECT all boots, sandals (wrong use case)
• "evening dress" → REJECT all tops, skirts (wrong category)

BE RUTHLESS: When in doubt, REJECT. Better to show 3 perfect matches than 10 wrong items.
Trust is everything - one wrong category match destroys user confidence.

Return ONLY the numbers of products that are PERFECT CATEGORY MATCHES (e.g., "2, 7, 15"):"""

            response = model.generate_content(prompt)
            
            if response and response.text:
                try:
                    # Parse numbers from LLM response
                    import re
                    numbers = re.findall(r'\b\d+\b', response.text.strip())
                    relevant_indices = [int(n) - 1 for n in numbers if 0 <= int(n) - 1 < len(products)]
                    
                    filtered_products = [products[i] for i in relevant_indices]
                    
                    print(f"   🤖 AGGRESSIVE LLM: {len(products)} → {len(filtered_products)} PERFECT matches")
                    
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
        """Create simplified product list for LLM processing"""
        product_list = []
        
        for i, product in enumerate(products):
            # Only include the MOST RELEVANT fields for LLM filtering
            name = product.get('product_name', '').strip()
            product_type = product.get('product_type', '').strip()
            tags = product.get('tags', [])[:4]  # Top 4 tags only
            
            # NEW: Get variant information
            available_sizes = product.get('available_sizes', [])
            available_colors = product.get('available_colors', [])
            
            # Create a SIMPLE, focused description for the LLM
            product_summary = f"{i+1}. {name}"
            
            # Add type if it's different from name and adds value
            if product_type and product_type.lower() not in name.lower():
                product_summary += f" ({product_type})"
            
            # Add sizes if available and relevant (clothing items)
            if available_sizes and len(available_sizes) <= 6:  # Don't overwhelm with too many sizes
                product_summary += f" [Sizes: {', '.join(available_sizes)}]"
            
            # Add colors if available and not already in name
            if available_colors and len(available_colors) <= 4:  # Limit colors shown
                name_lower = name.lower()
                relevant_colors = [color for color in available_colors 
                                 if color.lower() not in name_lower]
                if relevant_colors:
                    product_summary += f" [Colors: {', '.join(relevant_colors)}]"
            
            # Add key tags that aren't already in name/type/variants
            relevant_tags = []
            name_lower = name.lower()
            type_lower = product_type.lower()
            variant_text = ' '.join(available_sizes + available_colors).lower()
            
            for tag in tags:
                tag_clean = tag.strip().lower()
                if (tag_clean and 
                    len(tag_clean) > 2 and 
                    tag_clean not in name_lower and 
                    tag_clean not in type_lower and
                    tag_clean not in variant_text and
                    len(relevant_tags) < 2):  # Reduced to 2 tags max
                    relevant_tags.append(tag.strip())
            
            if relevant_tags:
                product_summary += f" [Tags: {', '.join(relevant_tags)}]"
            
            product_list.append(product_summary)
        
        return product_list
    
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
    
    def _strict_category_prefilter(self, products: List[Dict], query: str) -> List[Dict]:
        """STEP 1: Extremely strict category validation to catch obvious mismatches"""
        query_lower = query.lower().strip()
        
        # Define strict category rules
        category_rules = {
            # Outerwear categories
            'jacket': ['jacket', 'blazer', 'coat', 'windbreaker', 'bomber', 'denim jacket', 'leather jacket'],
            'coat': ['coat', 'jacket', 'parka', 'trench', 'overcoat', 'peacoat', 'windbreaker'],
            'blazer': ['blazer', 'jacket', 'suit jacket', 'sport coat'],
            
            # Bottom categories  
            'jeans': ['jeans', 'denim', 'jean', 'denim pants'],
            'pants': ['pants', 'trousers', 'slacks', 'chinos', 'joggers'],
            'leggings': ['leggings', 'tights', 'yoga pants'],
            'shorts': ['shorts', 'bermuda', 'cargo shorts'],
            'skirt': ['skirt', 'mini skirt', 'maxi skirt', 'pencil skirt'],
            
            # Top categories
            'dress': ['dress', 'gown', 'midi dress', 'maxi dress', 'mini dress'],
            'shirt': ['shirt', 'blouse', 'button up', 'button down', 'dress shirt'],
            'top': ['top', 'blouse', 'tank', 'camisole', 'tee', 't-shirt'],
            'sweater': ['sweater', 'pullover', 'jumper', 'cardigan', 'knitwear'],
            'hoodie': ['hoodie', 'sweatshirt', 'pullover hoodie'],
            
            # Footwear
            'shoes': ['shoes', 'sneakers', 'boots', 'heels', 'flats', 'sandals'],
            'boots': ['boots', 'ankle boots', 'knee boots', 'combat boots'],
            'sneakers': ['sneakers', 'trainers', 'athletic shoes', 'running shoes'],
            
            # Accessories
            'bag': ['bag', 'purse', 'handbag', 'backpack', 'tote', 'crossbody'],
            'belt': ['belt', 'waist belt', 'leather belt'],
            'hat': ['hat', 'cap', 'beanie', 'baseball cap', 'fedora'],
        }
        
        # Find the main category from query
        main_category = None
        for category, keywords in category_rules.items():
            if any(keyword in query_lower for keyword in keywords):
                main_category = category
                break
        
        if not main_category:
            print(f"   ⚠️  No specific category detected in '{query}', skipping strict filter")
            return products
        
        allowed_keywords = category_rules[main_category]
        print(f"   🎯 Strict category filter for '{main_category}': allowing only {allowed_keywords}")
        
        # Define category conflicts (these should NEVER match)
        category_conflicts = {
            'jacket': ['jeans', 'dress', 'skirt', 'pants', 'shorts', 'leggings', 'shoes', 'boots', 'bag'],
            'coat': ['jeans', 'dress', 'skirt', 'pants', 'shorts', 'leggings', 'shoes', 'boots', 'bag'],
            'jeans': ['jacket', 'coat', 'dress', 'skirt', 'shoes', 'boots', 'bag', 'hat'],
            'dress': ['jeans', 'pants', 'shorts', 'jacket', 'coat', 'shoes', 'boots', 'bag'],
            'pants': ['dress', 'skirt', 'jacket', 'coat', 'shoes', 'boots', 'bag'],
            'shoes': ['jeans', 'pants', 'dress', 'jacket', 'coat', 'shirt', 'top'],
            'bag': ['jeans', 'pants', 'dress', 'jacket', 'coat', 'shirt', 'shoes'],
        }
        
        conflict_keywords = category_conflicts.get(main_category, [])
        
        filtered_products = []
        rejected_count = 0
        
        for product in products:
            # Get searchable text
            name = product.get('product_name', '').lower()
            product_type = product.get('product_type', '').lower()
            tags = ' '.join(product.get('tags', [])).lower()
            description = product.get('description', '').lower()
            
            searchable_text = f"{name} {product_type} {tags} {description}"
            
            # Check for category conflicts first (immediate rejection)
            has_conflict = any(conflict in searchable_text for conflict in conflict_keywords)
            
            if has_conflict:
                conflicting_terms = [conflict for conflict in conflict_keywords if conflict in searchable_text]
                print(f"   🚫 REJECT: {name[:40]}... (conflicts: {conflicting_terms})")
                rejected_count += 1
                continue
            
            # Check if it matches the required category
            has_category_match = any(keyword in searchable_text for keyword in allowed_keywords)
            
            if has_category_match:
                print(f"   ✅ KEEP: {name[:40]}... (category match)")
                filtered_products.append(product)
            else:
                print(f"   ❌ REJECT: {name[:40]}... (no category match)")
                rejected_count += 1
        
        print(f"   📊 Strict filter: {len(products)} → {len(filtered_products)} products ({rejected_count} rejected for category mismatch)")
        return filtered_products
    
    def _basic_filter_by_query(self, products: List[Dict], query: str) -> List[Dict]:
        """Enhanced basic keyword-based filtering with ULTRA-STRICT category matching"""
        if not query.strip():
            return products
        
        # Parse query for specific attributes
        query_lower = query.lower()
        query_words = [word.strip() for word in query_lower.split() if len(word.strip()) >= 2]
        
        # STEP 1: Apply same strict category filtering as LLM version
        products = self._strict_category_prefilter(products, query)
        
        if not products:
            print(f"   ⚠️  No products survived strict category filtering")
            return []
        
        # STEP 2: Extract specific attributes from query
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
            
            # Check if ALL required attributes are present - ULTRA STRICT
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
        
        print(f"   📊 ULTRA-STRICT basic filtering: {len(products)} → {len(filtered_products)} products")
        return filtered_products 