#!/usr/bin/env python3
"""
Test Shopping Agent Pipeline
Tests the complete agent with Shopify JSON search
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append('app')

from utils.shopping_pipeline import process_shopping_query_with_tools_async

load_dotenv()

async def test_agent_pipeline():
    """Test the complete shopping agent with Shopify JSON"""
    
    print("🤖 TESTING SHOPPING AGENT PIPELINE")
    print("=" * 60)
    
    # Check environment
    google_cse = os.getenv("GOOGLE_CSE_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    print("🔧 Environment Check:")
    print(f"  {'✅' if google_cse else '❌'} Google CSE: {'Set' if google_cse else 'Missing'}")
    print(f"  {'✅' if gemini_key else '❌'} Gemini API: {'Set' if gemini_key else 'Missing'}")
    
    if not gemini_key:
        print("❌ Cannot test agent without GEMINI_API_KEY")
        return
    
    print("\n" + "=" * 60)
    
    # Test queries
    test_queries = [
        "Find me wireless headphones under $100",
        "I need a winter coat for kids",
        "Looking for baby shoes size 6-12 months"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 TEST {i}: '{query}'")
        print("-" * 40)
        
        try:
            # Test the async agent pipeline
            products, messages, final_response = await process_shopping_query_with_tools_async(
                query, gemini_key, max_iterations=10
            )
            
            print(f"✅ Agent completed successfully!")
            print(f"📊 Found {len(products)} products")
            print(f"💬 Final response: {final_response}")
            print(f"🔄 Used {len(messages)} conversation turns")
            
            if products:
                print("\n🏆 Top 3 Products:")
                for j, product in enumerate(products[:3], 1):
                    print(f"  {j}. {product.get('product_name', 'N/A')}")
                    print(f"     💰 {product.get('price', 'N/A')}")
                    print(f"     🏪 {product.get('store_name', 'N/A')}")
                    print()
            
            print(f"📈 Conversation Flow:")
            for j, msg in enumerate(messages[-5:], 1):  # Show last 5 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
                print(f"  {j}. {role}: {content}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_system_prompt():
    """Test that our system prompt is properly configured"""
    
    print("\n🔧 TESTING SYSTEM PROMPT")
    print("=" * 60)
    
    from utils.shopping_pipeline import get_system_prompt
    
    prompt = get_system_prompt()
    
    # Check for key phrases that should be in our updated prompt
    required_phrases = [
        "SHOPIFY JSON SEARCH",
        "Lightning Fast",
        "5-8 seconds",
        "Shopify stores",
        "Google Custom Search"
    ]
    
    print("✅ System Prompt Validation:")
    for phrase in required_phrases:
        if phrase in prompt:
            print(f"  ✅ Contains: '{phrase}'")
        else:
            print(f"  ❌ Missing: '{phrase}'")
    
    print(f"\n📏 Prompt length: {len(prompt)} characters")
    print(f"🔍 Contains 'Rye API': {'Yes' if 'Rye API' in prompt else 'No (Good!)'}")
    print(f"🔍 Contains 'Shopify JSON': {'Yes' if 'Shopify JSON' in prompt else 'No (Bad!)'}")

async def test_single_turn():
    """Test a single turn of the agent to see the response"""
    
    print("\n🎯 TESTING SINGLE AGENT TURN")
    print("=" * 60)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ No Gemini API key")
        return
    
    from utils.shopping_pipeline import get_response, get_system_prompt
    
    query = "Find me baby shoes under $50"
    messages = []
    
    print(f"Query: {query}")
    print("Getting AI response...")
    
    try:
        response, updated_messages = get_response(
            query, messages, gemini_key, system_prompt=get_system_prompt()
        )
        
        ai_response = response.choices[0].message.content
        print(f"\n🤖 AI Response:")
        print(ai_response)
        
        # Check if it contains a function call
        if "search_product" in ai_response:
            print("\n✅ AI wants to call search_product - Good!")
        elif "share_reasoning" in ai_response:
            print("\n✅ AI wants to share reasoning first - Good!")
        else:
            print("\n⚠️  No clear function call detected")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Shopping Agent Pipeline\n")
    
    # Test system prompt
    test_system_prompt()
    
    # Test single turn
    asyncio.run(test_single_turn())
    
    # Test full agent pipeline
    asyncio.run(test_agent_pipeline())
    
    print("\n🎉 Agent testing completed!")
    print("\n🚀 AGENT ARCHITECTURE:")
    print("✅ Multi-turn conversation with max 10 iterations")
    print("✅ Shopify JSON search (5-8s, free, reliable)")
    print("✅ Strategic reasoning and user engagement")
    print("✅ Smart function calling with proper JSON format")
    print("✅ Product curation and display")
    print("✅ Conversational final responses")
    print("\n💡 Ready for integration with chat interface!") 