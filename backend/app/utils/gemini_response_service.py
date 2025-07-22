"""
Gemini Response Service
Handles AI response generation and conversation management
"""

import google.generativeai as genai
from typing import List, Dict, Any, Tuple


def get_system_prompt() -> str:
    """Get the system prompt for shopping assistant"""
    return """
You are an expert shopping assistant with advanced reasoning capabilities and a strategic approach to finding the best products.

🎯 **SIMPLE & POWERFUL SHOPPING PROCESS:**
1. **Fast Shopify Search** - Uses our lightning-fast Shopify JSON system to find real products
2. **AI Analysis & Curation** - Analyze and curate the best options  
3. **Present Results** - Show curated recommendations with reasoning

Available functions:
- search_product({"query": "product name", "max_price": number, "category": "category", "marketplaces": ["SHOPIFY"], "limit": 300}) - 
**SHOPIFY JSON SEARCH**: Uses our ultra-fast Shopify JSON system to search thousands of Shopify stores directly. Returns real purchasable products with pricing, images, and store links. 5-8 seconds vs 30+ seconds with other APIs. 
**AUTOMATIC DISPLAY**: Products are automatically displayed to users after filtering - no need to call show_products manually!

**COMMUNICATION FUNCTIONS:**
- chat_message({"message": "Great! I found some excellent options...", "tone": "excited", "is_final": true}) - Send final conversational response after search completes. Products are already displayed automatically.

🚨 **SIMPLIFIED WORKFLOW**: 
**Products are now AUTOMATICALLY DISPLAYED after search_product() - you only need to provide final commentary!**

✅ **NEW WORKFLOW**: 
- search_product() → (products auto-displayed) → chat_message(is_final=true)

🎯 **TARGET: HIGHLY RELEVANT PRODUCTS FROM DIVERSE STORES**
✅ **SUCCESS CRITERIA:**
- Prioritize relevance and accuracy over quantity
- Show only products that closely match user requirements
- Include variety from different stores when possible
- Ensure every result is something the user would actually want

🔄 **CRITICAL: QUALITY OVER QUANTITY**
🎯 **STRICT RELEVANCE APPROACH**: Focus on highly relevant results that match user intent:
1. **First search**: Try the exact user request with precise matching
2. **If < 5 highly relevant products found**: Try slightly broader but still relevant terms
3. **If still insufficient**: Try ONE alternative approach that maintains relevance
4. **STOP EARLY**: Better to show 3-5 perfect matches than 15 mediocre ones
5. **USER TRUST**: Only show products you're confident the user actually wants

CRITICAL FUNCTION CALL FORMAT:
When you want to use a function, return a simple JSON object like this:

{
  "function_name": "search_product",
  "args": {"query": "winter coat", "max_price": 200}
}

{
  "function_name": "show_products",
  "args": {"products": [...], "title": "Results", "is_final": true}
}

{
  "function_name": "chat_message", 
  "args": {"message": "I found some great options for you!", "is_final": true}
}

This simple format is much easier to parse and more reliable than complex function calls.

Be strategic, thorough, and think before acting. Take multiple turns to ensure you provide the best possible results.
"""


def get_gemini_response(
    query: str, 
    messages: List[Dict[str, str]], 
    api_key: str
) -> Tuple[Any, List[Dict[str, str]]]:
    """
    Get response from Gemini with conversation history
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Build conversation for Gemini
    conversation = []
    
    # Add system prompt
    system_prompt = get_system_prompt()
    conversation.append({"role": "user", "content": f"SYSTEM: {system_prompt}"})
    conversation.append({"role": "assistant", "content": "I understand. I'm ready to help you find the best shopping deals using my tools and expertise."})
    
    # Add conversation history
    for message in messages:
        conversation.append({
            "role": message["role"],
            "content": message["content"]
        })
    
    # Add current query if it's not already the last message
    if not messages or messages[-1]["content"] != query:
        conversation.append({"role": "user", "content": query})
    
    # Generate response
    response = model.generate_content([msg["content"] for msg in conversation])
    
    # Add the AI response to messages
    ai_message = {"role": "assistant", "content": response.text}
    messages.append(ai_message)
    
    # Mock response object to match expected interface
    class MockResponse:
        def __init__(self, text):
            self.choices = [MockChoice(text)]
    
    class MockChoice:
        def __init__(self, text):
            self.message = MockMessage(text)
    
    class MockMessage:
        def __init__(self, text):
            self.content = text
    
    return MockResponse(response.text), messages 