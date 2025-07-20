#!/usr/bin/env python3
"""
Test script for structured products processing
Run this to test if the product processing is working correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.gemini_tools_converter import ShoppingContextVariables, _add_structured_products, get_structured_products_json

def test_structured_products():
    """Test structured products processing"""
    print("Testing structured products processing...")
    
    # Create test context
    context = ShoppingContextVariables()
    
    # Create test product data (similar to what AI would provide)
    test_products = [
        {
            "name": "CROPPED VEST WITH HIDDEN BUTTONS - Gray",
            "price": "$19.96",
            "image_url": "https://static.zara.net/assets/public/85eb/613c/4875466385c2/f32ffbb59334/01478124802-p/01478124802-p.jpg?ts=1740595714425&w=1824",
            "product_url": "https://www.zara.com/us/en/cropped-vest-with-hidden-buttons-p01478124.html",
            "description": "Cropped vest in gray with hidden buttons. Perfect for a modern, layered look."
        },
        {
            "name": "ZIP-UP BLAZER WITH SHOULDER PADS - Black",
            "price": "$31.96",
            "image_url": "https://static.zara.net/assets/public/5991/9680/cd8b4865b184/cb22e0ca2983/02517791800-p/02517791800-p.jpg?ts=1740595711886&w=1824",
            "product_url": "https://www.zara.com/us/en/zip-up-blazer-with-shoulder-pads-p02517791.html",
            "description": "Black zip-up blazer with shoulder pads for a structured silhouette."
        }
    ]
    
    arguments = {"products": test_products}
    
    # Test the function
    try:
        result = _add_structured_products(arguments, context)
        print(f"✅ Function result: {result}")
        print(f"✅ Context deals found: {len(context.deals_found)}")
        
        print("\nDeals in context:")
        for i, deal in enumerate(context.deals_found):
            print(f"  Deal {i+1}:")
            print(f"    Type: {deal.get('type')}")
            print(f"    Name: {deal.get('product_name')}")
            print(f"    Price: {deal.get('price')}")
            print(f"    Image: {deal.get('image_url')[:60]}..." if deal.get('image_url') else "    Image: None")
        
        # Test the structured products JSON function
        structured_products = get_structured_products_json(context)
        print(f"\n✅ Structured products for frontend: {len(structured_products)}")
        
        if structured_products:
            print("\nFrontend products:")
            for i, product in enumerate(structured_products):
                print(f"  Product {i+1}:")
                print(f"    ID: {product.get('id')}")
                print(f"    Product Name: {product.get('product_name')}")
                print(f"    Name: {product.get('name')}")
                print(f"    Price: {product.get('price')}")
                print(f"    Store: {product.get('store')}")
                print(f"    Image URL: {product.get('image_url')[:60]}..." if product.get('image_url') else "    Image URL: None")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing structured products: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🧪 Testing Structured Products Processing")
    print("="*50)
    
    test_result = test_structured_products()
    
    print("\n" + "="*50)
    print(f"📊 Test Result: {'✅ PASS' if test_result else '❌ FAIL'}")
    
    if test_result:
        print("\n🎉 Structured products processing is working correctly!")
    else:
        print("\n⚠️ There's an issue with structured products processing.") 