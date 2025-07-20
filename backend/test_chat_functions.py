"""
Test the new chat functions: chat_message and show_products
"""

from app.utils.gemini_tools_converter import (
    ShoppingContextVariables,
    execute_function_with_context
)

def test_chat_message():
    """Test the chat_message function"""
    print("💬 Testing chat_message function...")
    
    context = ShoppingContextVariables()
    
    # Test progress update
    arguments = {
        "message": "Great! I'm finding some promising options across multiple stores...",
        "tone": "excited",
        "includes_reasoning": False,
        "is_final": False
    }
    
    result = execute_function_with_context("chat_message", arguments, context)
    print(f"Progress update result: {result}")
    
    # Test final message
    final_arguments = {
        "message": "Perfect! I found fantastic options for you!",
        "tone": "celebratory", 
        "includes_reasoning": False,
        "is_final": True
    }
    
    final_result = execute_function_with_context("chat_message", final_arguments, context)
    print(f"Final message result: {final_result}")
    
    # Check context
    print(f"Chat updates stored: {len(getattr(context, 'chat_updates', []))}")
    print(f"Final chat message: {context.final_chat_message}")
    
    if hasattr(context, 'chat_updates') and context.chat_updates:
        print("Chat updates:")
        for update in context.chat_updates:
            print(f"  - {update['message']} ({update['tone']})")
    
    return bool(context.final_chat_message)

def test_show_products():
    """Test the show_products function"""
    print("\n📱 Testing show_products function...")
    
    context = ShoppingContextVariables()
    
    sample_products = [
        {
            "name": "Sony WH-1000XM4",
            "price": "$279.99",
            "store": "Best Buy",
            "image_url": "https://example.com/sony.jpg",
            "product_url": "https://bestbuy.com/sony",
            "description": "Premium noise-canceling headphones",
            "badge": "Editor's Pick",
            "reasoning": "Best overall sound quality"
        },
        {
            "name": "Apple AirPods Pro", 
            "price": "$199.99",
            "store": "Target",
            "image_url": "https://example.com/airpods.jpg",
            "product_url": "https://target.com/airpods",
            "description": "True wireless with spatial audio",
            "badge": "Most Popular",
            "reasoning": "Perfect for Apple users"
        }
    ]
    
    arguments = {
        "products": sample_products,
        "title": "Best Headphones Found",
        "subtitle": "Curated for different needs",
        "is_final": True
    }
    
    result = execute_function_with_context("show_products", arguments, context)
    print(f"Show products result: {result}")
    
    # Check context
    print(f"Products in context: {len(context.deals_found)}")
    print(f"Has final products flag: {getattr(context, 'has_final_products', False)}")
    
    if context.deals_found:
        print("Sample product stored:")
        product = context.deals_found[0]
        print(f"  Name: {product.get('product_name', 'N/A')}")
        print(f"  Badge: {product.get('badge', 'N/A')}")
        print(f"  Reasoning: {product.get('reasoning', 'N/A')}")
    
    return len(context.deals_found) > 0

def test_function_detection():
    """Test if the function detection works"""
    print("\n🔍 Testing Function Detection...")
    
    from app.utils.gemini_tools_converter import extract_tool_call_from_response
    
    # Test responses that should be detected
    test_responses = [
        'chat_message({"message": "I found great options!", "tone": "excited"})',
        'show_products({"products": [...], "title": "Results", "is_final": true})',
        '```tool_code\nchat_message({"message": "Testing"})\n```',
        'Let me share my progress: chat_message({"message": "Working on it...", "tone": "informative"})'
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\nTest {i}: {response[:50]}...")
        tool_call = extract_tool_call_from_response(response)
        
        if tool_call:
            print(f"  ✅ Detected: {tool_call['function_name']}")
        else:
            print(f"  ❌ Not detected")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing New Chat Functions")
    print("=" * 50)
    
    # Run tests
    chat_test = test_chat_message()
    products_test = test_show_products()
    detection_test = test_function_detection()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"chat_message(): {'✅ PASS' if chat_test else '❌ FAIL'}")
    print(f"show_products(): {'✅ PASS' if products_test else '❌ FAIL'}")
    print(f"Function Detection: {'✅ PASS' if detection_test else '❌ FAIL'}")
    
    if all([chat_test, products_test, detection_test]):
        print("\n✅ All new chat functions are working!")
        print("💡 If the AI isn't using them, it might be:")
        print("   1. Still learning the new function names")
        print("   2. Preferring familiar functions")
        print("   3. Need explicit instruction to use new functions")
    else:
        print("\n❌ Some functions have issues - check above for details") 