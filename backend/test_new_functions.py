"""
Test the new frontend functions: display_products and share_reasoning
"""

from app.utils.gemini_tools_converter import (
    ShoppingContextVariables,
    _display_products,
    _share_reasoning,
    get_structured_products_json
)

def test_display_products():
    """Test the display_products function"""
    print("🖼️ Testing display_products function...")
    
    # Create context
    context = ShoppingContextVariables()
    
    # Sample products to display
    sample_products = [
        {
            "name": "Sony WH-1000XM4 Wireless Headphones",
            "price": "$279.99",
            "store": "Best Buy",
            "image_url": "https://example.com/sony-headphones.jpg",
            "product_url": "https://bestbuy.com/sony-wh1000xm4",
            "description": "Premium noise-canceling headphones with 30-hour battery",
            "badge": "Editor's Pick",
            "reasoning": "Best overall for noise canceling and sound quality",
            "availability": "in stock",
            "brand": "Sony",
            "category": "Electronics"
        },
        {
            "name": "Apple AirPods Pro (2nd Gen)",
            "price": "$199.99",
            "store": "Target",
            "image_url": "https://example.com/airpods-pro.jpg", 
            "product_url": "https://target.com/airpods-pro-2nd-gen",
            "description": "True wireless with adaptive transparency and spatial audio",
            "badge": "Most Popular",
            "reasoning": "Perfect for Apple ecosystem users",
            "availability": "in stock",
            "brand": "Apple",
            "category": "Electronics"
        },
        {
            "name": "Anker Soundcore Life Q30",
            "price": "$59.99",
            "store": "Amazon",
            "image_url": "https://example.com/anker-q30.jpg",
            "product_url": "https://amazon.com/anker-soundcore-q30", 
            "description": "Active noise canceling with 40-hour playtime",
            "badge": "Best Value",
            "reasoning": "Excellent features at budget price point",
            "availability": "in stock", 
            "brand": "Anker",
            "category": "Electronics"
        }
    ]
    
    # Test the display_products function
    arguments = {
        "products": sample_products,
        "title": "Best Wireless Headphones",
        "subtitle": "Curated for different budgets and needs"
    }
    
    result = _display_products(arguments, context)
    
    print(f"Function result: {result}")
    print(f"Products added to context: {len(context.deals_found)}")
    
    # Check structured products
    structured = get_structured_products_json(context)
    print(f"Structured products for frontend: {len(structured)}")
    
    for i, product in enumerate(structured, 1):
        print(f"\n{i}. {product['product_name']}")
        print(f"   Price: {product['price']}")
        print(f"   Store: {product['store']}")
        print(f"   Badge: {context.deals_found[i-1].get('badge', 'N/A')}")
        print(f"   Reasoning: {context.deals_found[i-1].get('reasoning', 'N/A')}")
    
    return len(structured) == 3

def test_share_reasoning():
    """Test the share_reasoning function"""
    print("\n💭 Testing share_reasoning function...")
    
    # Create context
    context = ShoppingContextVariables()
    
    # Sample reasoning
    arguments = {
        "type": "analysis",
        "title": "How I Selected These Headphones",
        "steps": [
            "Searched across 4 different strategies for comprehensive coverage",
            "Found 25+ options from Amazon, Best Buy, Target, and specialty audio stores", 
            "Filtered by price range, customer reviews (4+ stars), and brand reputation",
            "Considered different use cases: premium, popular, and budget-friendly",
            "Checked current availability and pricing accuracy"
        ],
        "conclusion": "Selected 3 diverse options that offer the best value in their respective price ranges",
        "confidence": "high"
    }
    
    result = _share_reasoning(arguments, context)
    
    print(f"Function result: {result}")
    print(f"Final chat message length: {len(context.final_chat_message) if context.final_chat_message else 0}")
    print(f"Reasoning chains stored: {len(getattr(context, 'reasoning_chains', []))}")
    
    if context.final_chat_message:
        print("\nFormatted reasoning output:")
        print("-" * 50)
        print(context.final_chat_message)
        print("-" * 50)
    
    return bool(context.final_chat_message)

def test_comparison_reasoning():
    """Test reasoning with comparison type"""
    print("\n🔍 Testing comparison reasoning...")
    
    context = ShoppingContextVariables()
    
    arguments = {
        "type": "comparison", 
        "title": "Premium vs Budget Options",
        "steps": [
            {"text": "Sony WH-1000XM4 offers superior noise canceling but costs $280", "icon": "🎧"},
            {"text": "Anker Soundcore Q30 has good noise canceling for only $60", "icon": "💰"},
            {"text": "Apple AirPods Pro best for iPhone users at $200 middle ground", "icon": "📱"}
        ],
        "conclusion": "Each serves different needs - premium features vs budget value vs ecosystem integration",
        "confidence": "medium"
    }
    
    result = _share_reasoning(arguments, context)
    
    print(f"Comparison result: {result}")
    if context.final_chat_message:
        print("\nComparison reasoning:")
        print(context.final_chat_message)
    
    return "comparison" in result.lower()

if __name__ == "__main__":
    print("Testing New Frontend Functions")
    print("=" * 50)
    
    # Run tests
    test1 = test_display_products()
    test2 = test_share_reasoning() 
    test3 = test_comparison_reasoning()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Display Products: {'PASS' if test1 else 'FAIL'}")
    print(f"Share Reasoning: {'PASS' if test2 else 'FAIL'}")
    print(f"Comparison Reasoning: {'PASS' if test3 else 'FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n✅ All new functions working correctly!")
        print("Ready to integrate with frontend for:")
        print("  📱 Visual product displays with badges")
        print("  💭 Transparent reasoning chains")
        print("  🎯 Enhanced user experience")
    else:
        print("\n⚠️ Some functions need attention") 