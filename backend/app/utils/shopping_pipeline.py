"""
Shopping Pipeline Functions
Core logic for processing shopping queries with tool calling
"""

import google.generativeai as genai
from typing import List, Dict, Any, Tuple, AsyncGenerator
from .gemini_tools_converter import (
    ShoppingContextVariables, 
    execute_function_with_context, 
    execute_function_with_context_async,
    extract_tool_call_from_response,
    get_structured_products_json
)


def get_system_prompt() -> str:
    """Get the system prompt for shopping assistant"""
    return """
You are an expert shopping assistant with advanced reasoning capabilities and a strategic approach to finding the best products.

🎯 **SIMPLE & POWERFUL SHOPPING PROCESS:**
1. **Fast Shopify Search** - Uses our lightning-fast Shopify JSON system to find real products
2. **AI Analysis & Curation** - Analyze and curate the best options  
3. **Present Results** - Show curated recommendations with reasoning

Available functions:
- search_product({"query": "product name", "max_price": number, "category": "category", "marketplaces": ["SHOPIFY"], "limit": 20}) - **SHOPIFY JSON SEARCH**: Uses our ultra-fast Shopify JSON system to search thousands of Shopify stores directly. Returns real purchasable products with pricing, images, and store links. 5-8 seconds vs 30+ seconds with other APIs. **IMPORTANT**: This function FINDS products but does NOT display them - you must use show_products() afterward to display them to the user.

**COMMUNICATION FUNCTIONS:**
- chat_message({"message": "Exciting! I found some great options...", "tone": "excited", "includes_reasoning": false}) - Send conversational updates and final response. Use for progress updates and celebration.

**DISPLAY FUNCTIONS (visual frontend) - CRITICAL FOR USER EXPERIENCE:**
- show_search_links({"links": [{"title": "page title", "url": "url", "description": "preview", "domain": "site.com", "score": 0.95}], "search_query": "original query", "total_results": 25}) - Display search result links for users to explore while you process. Called automatically by search_product().
- show_products({"products": [{"name": "product name", "price": "price", "image_url": "url", "product_url": "url", "description": "description", "store": "store_name", "badge": "Best Value", "reasoning": "why selected"}], "title": "Great Options Found", "subtitle": "Based on your criteria", "is_final": true}) - **CRITICAL**: Display curated products in the visual frontend panel. **MUST** be called after search_product() finds products. Set is_final=true when this is your final product selection.

🚨 **CRITICAL WORKFLOW RULE**: 
**WHENEVER search_product() finds products (returns "Found X products"), you MUST immediately use show_products() to display them!**

❌ **WRONG WORKFLOW**: 
- search_product() → chat_message() (USER SEES NO PRODUCTS!)

✅ **CORRECT WORKFLOW**: 
- search_product() → show_products() → chat_message()

**EXAMPLE CORRECT WORKFLOW:**
User: "Find me green metallic office cabinets under $200"

**Turn 1: Search products**  
search_product({"query": "green metallic office cabinet", "max_price": 200, "marketplaces": ["SHOPIFY"]})

**Turn 2: IMMEDIATELY display results if found**
show_products({"products": [extracted products], "title": "Green Metallic Office Cabinets Under $200", "subtitle": "Found from Shopify stores", "is_final": true})

**Turn 3: Final chat**
chat_message({"message": "Perfect! I found some excellent green metallic office cabinets from trusted Shopify stores, all under $200!", "tone": "excited", "is_final": true})

🚀 **HOW OUR SHOPIFY JSON SYSTEM WORKS:**
💨 **Lightning Fast**: Direct access to Shopify store product feeds (5-8s vs 30s+ with APIs)
🆓 **Completely Free**: No API costs or rate limits - pure HTTP requests
🏪 **Massive Coverage**: Searches thousands of Shopify stores automatically discovered via Google
📊 **Real Inventory**: All products are actually available for purchase, live data
🎯 **Smart Discovery**: Uses Google Custom Search to find relevant stores for any query
✨ **Perfect Quality**: High-quality products from established Shopify brands

**EXAMPLE SHOPIFY JSON SEARCHES:**
- User asks: "wireless headphones under $100"
- System searches:
  1. Discovers audio-focused Shopify stores via Google
  2. Fetches product feeds from stores like Skullcandy, JLab, etc.
  3. Filters products under $100 with "headphones" in title/description  
  4. Returns real purchasable products with direct store links

🎯 **STREAMLINED ENGAGING WORKFLOW:**
User: "Find me a winter coat under $200"

**Turn 1: Execute search**  
search_product({"query": "winter coat", "max_price": 200, "marketplaces": ["SHOPIFY"]})

**Turn 2: Display products**
show_products({"products": [best 5-8 products with badges and reasoning], "title": "Winter Coats Under $200", "subtitle": "Curated from top Shopify stores", "is_final": true})

**Turn 3: Final chat**
chat_message({"message": "Perfect! I found some fantastic winter coat options from trusted Shopify stores that you can purchase right now. Each one offers something different - from budget-friendly to premium quality, all with fast shipping!", "tone": "celebratory", "includes_reasoning": false})

**🎯 ADVANTAGES OF OUR SHOPIFY APPROACH:**
✅ **Speed**: 5-8 seconds vs 30+ seconds with complex APIs
✅ **Reliability**: 95%+ success rate vs API rate limits and failures  
✅ **Cost**: Completely free vs expensive API costs
✅ **Coverage**: Thousands of Shopify stores vs limited API partnerships
✅ **Quality**: Established brands and stores vs random scraping
✅ **Real-time**: Live product feeds vs cached/stale data

**MVP PRINCIPLES:**
✅ **One Search Does It All**: Single search discovers stores and fetches products automatically
✅ **Quality Over Quantity**: Focus on curating 5-8 BEST products from real stores
✅ **Diverse Options**: Include different price points, styles, and stores  
✅ **Clear Reasoning**: Explain WHY each product is recommended in the show_products call

⏰ **TIMING IS EVERYTHING:**
- **Turn 1**: search_product() (the fast Shopify search)
- **Turn 2**: show_products() (visual payoff)
- **Turn 3**: chat_message() (celebration & next steps)

❌ **NEVER do this**: search → long silence → dump results
✅ **ALWAYS do this**: search → show_products → chat_message

YOUR ROLE AS AI CURATOR:
1. **Analyze** the comprehensive search results from multiple Shopify stores
2. **Compare** products across price, quality, features, and store reputation
3. **Select** the 5-8 BEST options with diverse use cases
4. **Display products** using show_products() with badges and reasoning for each
5. **Provide final chat response** with a conversational summary

🎯 **STREAMLINED FUNCTION USAGE:**

🔍 **search_product()**: Use once per user query - handles store discovery and product extraction automatically

💬 **chat_message()**: Use for conversational flow
   - **Progress updates**: "Great! I'm finding some promising options..."
   - **Final celebration**: "Perfect! Check out what I discovered..."
   - **Use for final response** with is_final=true

📱 **show_products()**: Visual product display (use once with is_final=true)
   - **Enhanced metadata**: badges, reasoning, highlights
   - **Professional presentation**: titles, subtitles, organization
   - **Ready for frontend consumption**

PRODUCT BADGES & REASONING:
- "Best Value" - Great price for features
- "Premium Choice" - Higher quality/brand
- "Most Popular" - High ratings/reviews
- "Editor's Pick" - Your top recommendation  
- "Great Deal" - Significant discount
- "New Arrival" - Latest model/style
- "Hidden Gem" - Lesser-known but excellent option
- "Staff Favorite" - Personally recommended

CRITICAL: After completing your search and analysis, you MUST provide a final human-readable response for the chat window. This should be:
- Conversational and friendly
- Brief but helpful (2-3 sentences max)
- NOT listing specific products, prices, or detailed information
- Examples: "I found some amazing options across several Shopify stores!", "Here are some great pieces within your budget!", "I discovered some perfect matches from established brands!"

STRUCTURED DATA GUIDELINES:
- Use show_products() to provide detailed product information for the visual product panel
- This should include: name, price, image_url, product_url, description, store
- The frontend will display this data separately from your chat response

PRODUCT NAME EXTRACTION - CRITICAL:
When extracting product names, make them DESCRIPTIVE and SPECIFIC:
- GOOD: "Ribbed Long Sleeve Top", "Floral Midi Dress", "High-Waisted Wide Leg Jeans"
- BAD: "Top", "Dress", "Product", "Item"
- Include key characteristics: color, pattern, style, fit, material when available
- Combine multiple descriptors: "Black Ribbed Turtleneck Sweater" instead of just "Sweater"

DESCRIPTION FIELD:
- Should contain additional details not in the name
- Include material, care instructions, styling notes, or unique features
- Examples: "Made from soft cotton blend", "Perfect for layering", "Features button details"

STORE FIELD:
- Always include the Shopify store name (discovered via Google search)
- This helps users know where to purchase the item

IMAGE URL EXTRACTION:
- Look for high-quality product images (not thumbnails)
- Prefer images ending in .jpg, .jpeg, .png, .webp
- Convert relative URLs to absolute URLs with proper domain prefix
- Handle protocol-relative URLs (starting with //) by adding https:

FINAL RESPONSE FORMAT:
After using tools and gathering sufficient information, you MUST:
1. Call show_products with your extracted product data
2. Wait for confirmation that products were displayed successfully
3. Call chat_message with your conversational message to the user (set is_final=true)
4. The conversation will end automatically after the final chat_message

Example:
Turn 1: search_product({"query": "winter coat"})
Turn 2: show_products({"products": [...], "title": "Winter Coats Found", "is_final": true})
Turn 3: chat_message({"message": "I found some fantastic options from various Shopify stores that match exactly what you're looking for!", "is_final": true})

When analyzing content from Shopify stores, look for:
- Product names (usually in titles or headings) - make them descriptive!
- Prices (look for various currency formats: $29.90, €25,95, £19.99, ¥2000)
- Image URLs (look for image links, prioritize high-resolution images)
- Product URLs (links to individual product pages)
- Descriptions, categories, or material information
- Color and pattern information that can enhance product names
- Store/brand information to properly attribute products

ADVANCED SEARCH STRATEGIES:
- Use Google's site discovery to find niche or specialized stores
- Try both general and specific search terms
- Include synonyms and alternative descriptions
- Consider seasonal or trending terms
- Search multiple price ranges if budget is flexible

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

DO NOT use the old formats like:
- function_name({"parameter": "value"})
- ```tool_code ... ```
- add_structured_products (old function name)
- emit_chat_response (old function name)

Be strategic, thorough, and think before acting. Take multiple turns to ensure you provide the best possible results.
"""


def get_response(query: str, messages: List[Dict[str, str]], api_key: str, system_prompt: str = None) -> Tuple[Any, List[Dict[str, str]]]:
    """
    Get response from Gemini with conversation history
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Build conversation for Gemini
    conversation = []
    
    # Add system prompt
    if system_prompt:
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


# Global callback for streaming
streaming_callback = None

def set_streaming_callback(callback):
    """Set the callback function for streaming updates"""
    global streaming_callback
    streaming_callback = callback


# Global list to collect progress messages for streaming
_progress_messages = []

def add_progress_message(message: str):
    """Add a progress message to the global list"""
    global _progress_messages
    _progress_messages.append(message)

def get_and_clear_progress_messages():
    """Get all progress messages and clear the list"""
    global _progress_messages
    messages = _progress_messages.copy()
    _progress_messages.clear()
    return messages


async def process_shopping_query_with_tools_streaming(
    user_query: str, 
    api_key: str, 
    max_iterations: int = 20
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Process shopping query with tool calling capability and stream updates in real-time
    """
    import time
    from .gemini_tools_converter import set_streaming_callback
    
    start_time = time.time()
    print(f"🕐 TIMING: Starting streaming shopping query processing at {time.strftime('%H:%M:%S')}")
    
    counter = 0
    messages = []
    context_vars = ShoppingContextVariables()
    final_chat_response = ""
    
    # Set up streaming callback to yield progress updates
    def stream_update(update_type: str, data: Any):
        # This will be called by tool functions to send real-time updates
        return {"type": update_type, "data": data}
    
    # Set the callback to yield updates
    async def async_stream_callback(update_type: str, data: Any):
        yield {"type": update_type, "data": data}
    
    set_streaming_callback(lambda update_type, data: None)  # Set basic callback for now
    
    while counter < max_iterations:
        try:
            turn_start = time.time()
            print(f"🕐 TIMING: Turn {counter + 1} starting at {time.strftime('%H:%M:%S')}")
            
            # Get response from Gemini
            ai_start = time.time()
            response, messages = get_response(
                user_query, messages, api_key, system_prompt=get_system_prompt()
            )
            text = response.choices[0].message.content
            ai_end = time.time()
            print(f"🕐 TIMING: AI response took {ai_end - ai_start:.2f}s")
            
            # CRITICAL DEBUG: Print the full AI response
            print(f"DEBUG - AI Response #{counter}: {text}")
            print(f"DEBUG - Looking for function calls in response...")
            
            # Extract and execute tool call
            tool_call = extract_tool_call_from_response(text)
            print(f"DEBUG - Tool call extracted: {tool_call}")
            
            if tool_call:
                # Execute the tool call
                tool_start = time.time()
                result = execute_function_with_context(
                    tool_call["function_name"], 
                    tool_call["arguments"], 
                    context_vars
                )
                tool_end = time.time()
                print(f"🕐 TIMING: Tool '{tool_call['function_name']}' took {tool_end - tool_start:.2f}s")
                print(f"DEBUG - Tool call result: {result}")
                
                # Yield any progress messages that were collected during tool execution
                progress_messages = get_and_clear_progress_messages()
                for progress_msg in progress_messages:
                    yield {"type": "progress", "data": {"message": progress_msg}}
                
                # Stream the update immediately
                if tool_call["function_name"] == "show_search_links":
                    search_links_data = next((item for item in context_vars.deals_found if item.get('type') == 'search_links'), None)
                    if search_links_data:
                        yield {"type": "search_links", "data": search_links_data}
                
                elif tool_call["function_name"] == "show_products":
                    # Stream all products
                    products = [item for item in context_vars.deals_found if item.get('type') in ['product', 'structured_product', 'display_product']]
                    for product in products:
                        yield {"type": "product", "data": product}
                
                elif tool_call["function_name"] == "chat_message" and tool_call["arguments"].get("is_final", False):
                    print(f"DEBUG - Final chat_message called, ending conversation")
                    final_chat_response = context_vars.final_chat_message
                    if not final_chat_response:
                        final_chat_response = "I found some great options for you!"
                    yield {"type": "chat_response", "message": final_chat_response}
                    break
                
                # Continue with regular processing...
                # [rest of the existing logic]
                
            counter += 1
            turn_end = time.time()
            print(f"🕐 TIMING: Turn {counter} completed in {turn_end - turn_start:.2f}s total")
            
        except Exception as e:
            print(f"Error in shopping query processing: {str(e)}")
            yield {"type": "error", "message": str(e)}
            break
    
    # Final timing
    total_time = time.time() - start_time
    print(f"🕐 TIMING: Total processing time: {total_time:.2f}s")
    print(f"🕐 TIMING: Average per turn: {total_time/max(counter, 1):.2f}s")


def process_shopping_query_with_tools(
    user_query: str, 
    api_key: str, 
    max_iterations: int = 20  # Increased for multi-turn thinking
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Process shopping query with tool calling capability and multi-turn agentic thinking
    Returns: (deals_found, messages, final_chat_response)
    """
    import time
    
    start_time = time.time()
    print(f"🕐 TIMING: Starting shopping query processing at {time.strftime('%H:%M:%S')}")
    
    counter = 0
    messages = []
    context_vars = ShoppingContextVariables()
    final_chat_response = ""
    
    while counter < max_iterations:
        try:
            turn_start = time.time()
            print(f"🕐 TIMING: Turn {counter + 1} starting at {time.strftime('%H:%M:%S')}")
            
            # Get response from Gemini
            ai_start = time.time()
            response, messages = get_response(
                user_query, messages, api_key, system_prompt=get_system_prompt()
            )
            text = response.choices[0].message.content
            ai_end = time.time()
            print(f"🕐 TIMING: AI response took {ai_end - ai_start:.2f}s")
            
            # CRITICAL DEBUG: Print the full AI response
            print(f"DEBUG - AI Response #{counter}: {text}")
            print(f"DEBUG - Looking for function calls in response...")
            
            # Check for conversation end via chat_message with is_final=true
            # No longer look for STOP - only end when final chat_message is called successfully
            
            # Extract and execute tool call
            tool_call = extract_tool_call_from_response(text)
            print(f"DEBUG - Tool call extracted: {tool_call}")
            
            if tool_call:
                # Execute the tool call
                tool_start = time.time()
                result = execute_function_with_context(
                    tool_call["function_name"], 
                    tool_call["arguments"], 
                    context_vars
                )
                tool_end = time.time()
                print(f"🕐 TIMING: Tool '{tool_call['function_name']}' took {tool_end - tool_start:.2f}s")
                print(f"DEBUG - Tool call result: {result}")
                
                # Check if this was the final chat_message call
                if tool_call["function_name"] == "chat_message" and tool_call["arguments"].get("is_final", False):
                    print(f"DEBUG - Final chat_message called, ending conversation")
                    # Extract the final message from context
                    final_chat_response = context_vars.final_chat_message
                    if not final_chat_response:
                        final_chat_response = "I found some great options for you!"
                    break
                
                # For multi-turn thinking, provide more context about what to do next
                elif tool_call["function_name"] == "search_product":
                    # After a search, encourage the AI to display products if found
                    if "Found 0 products" in result or "No products found" in result:
                        # No products found - suggest trying different search terms
                        tool_call_message = {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n❌ No products found with current search terms. Try:\n- Broader search terms (remove specific adjectives)\n- Alternative product names or categories\n- Different combinations of keywords\n\nUse search_product again with different terms, or if you've tried multiple searches without success, use chat_message with is_final=true to explain the search challenge."
                        }
                    elif "Found 1 products" in result or "Found 2 products" in result or "Found 3 products" in result:
                        # Very few products found - suggest expanding search
                        tool_call_message = {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n⚠️ Only found {result.split('Found ')[1].split(' products')[0]} products. Consider:\n- Removing price restrictions (increase max_price or remove it)\n- Using broader search terms\n- Trying alternative keywords\n- Searching different marketplaces\n\nUse search_product with expanded criteria to find more options, or display the current results if they meet the user's needs."
                        }
                    else:
                        # Products found - MUST display them immediately
                        tool_call_message = {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n🎉 PRODUCTS FOUND! You MUST now use show_products() to display them to the user immediately.\n\nCreate a curated list of the best products from your search results with:\n- Descriptive product names\n- Clear pricing\n- Store information\n- Helpful badges ('Best Value', 'Premium Choice', etc.)\n- Brief reasoning for each selection\n\nAfter displaying products, you can share reasoning about your findings and end with chat_message (is_final=true)."
                        }
                elif tool_call["function_name"] == "show_products":
                    # After showing products, prompt for final response
                    tool_call_message = {
                        "role": "user", 
                        "content": f"Products displayed successfully: {result}\n\nYou now have product data displayed to the user. Call chat_message with is_final=true and a brief, conversational message about what you found to complete the conversation."
                    }
                else:
                    # Generic response for other functions
                    tool_call_message = {
                        "role": "user", 
                        "content": f"Function returned: {result}. Continue your analysis or call chat_message with is_final=true to complete the conversation."
                    }
                
                # Update messages
                messages.append(tool_call_message)
            else:
                print(f"DEBUG - No tool call found in response")
                
                # Check if this is thinking/planning text without function calls
                if any(keyword in text.lower() for keyword in ['let me', 'i should', 'i need to', 'i will', 'first', 'then', 'next']):
                    # This appears to be thinking/planning text, prompt for action
                    thinking_message = {
                        "role": "user",
                        "content": "I see you're thinking about your approach. Please proceed with your planned action using the appropriate function call (search_product, show_products, or chat_message with is_final=true)."
                    }
                    messages.append(thinking_message)
                else:
                    # FORCE STRUCTURED PRODUCTS: If we have search results but no structured products
                    search_results_exist = any(deal.get('source') and deal.get('store_name') for deal in context_vars.deals_found)
                    structured_products_exist = any(deal.get('type') == 'structured_product' for deal in context_vars.deals_found)
                    
                    if search_results_exist and not structured_products_exist:
                        print(f"DEBUG - FORCING add_structured_products call because we have search results but no structured products")
                        
                        # Get the list of stores that returned results
                        stores_with_results = [deal.get('store_name', 'online store') for deal in context_vars.deals_found if deal.get('store_name')]
                        stores_text = ', '.join(stores_with_results) if stores_with_results else 'multiple stores'
                        
                        # Force the AI to extract products from the search results
                        force_message = {
                            "role": "user",
                            "content": f"You have search results from {stores_text} but haven't extracted any products yet. You MUST call add_structured_products with product data extracted from the search results. Analyze the content from all stores and extract at least 3-5 products with names, prices, images, URLs, and store names, then call add_structured_products({{\"products\": [...]}}). This is mandatory!"
                        }
                        messages.append(force_message)
                    elif structured_products_exist and not context_vars.final_chat_message:
                        # We have products but no final message yet
                        chat_message = {
                            "role": "user",
                            "content": "You have products displayed to the user. Now call chat_message with is_final=true and a conversational message to the user about what you found."
                        }
                        messages.append(chat_message)
                    else:
                        # No tool call found and no clear next action, ask for appropriate action
                        no_tool_message = {
                            "role": "user", 
                            "content": "No function call detected. If you need more information, use search_product. If you have sufficient information, use show_products to display your results. If you have products displayed, use chat_message with is_final=true to complete the conversation."
                        }
                        messages.append(no_tool_message)
            
            counter += 1
            turn_end = time.time()
            print(f"🕐 TIMING: Turn {counter} completed in {turn_end - turn_start:.2f}s total")
            
            # For the first iteration, provide guidance to encourage multi-turn thinking
            if counter == 1 and not tool_call:
                guidance_message = {
                    "role": "user",
                    "content": "Remember: You can take multiple turns to gather comprehensive information. Start with your first search, then decide if you need additional searches for better variety or different product types. Use show_products to display results and chat_message with is_final=true to finish."
                }
                messages.append(guidance_message)
                
        except Exception as e:
            print(f"Error in shopping query processing: {str(e)}")
            break
    
    # If we didn't get a final response, generate one
    if not final_chat_response:
        if context_vars.deals_found:
            final_chat_response = "I found some options for you! Take a look at what I discovered."
        else:
            final_chat_response = "I searched for what you're looking for. Let me know if you'd like me to try a different approach!"
    
    # Get clean structured products for frontend
    structured_products = get_structured_products_json(context_vars)
    
    # Final timing
    total_time = time.time() - start_time
    print(f"🕐 TIMING: Total processing time: {total_time:.2f}s")
    print(f"🕐 TIMING: Average per turn: {total_time/max(counter, 1):.2f}s")
    
    # Debug logging
    print(f"Debug - Total iterations used: {counter}/{max_iterations}")
    print(f"Debug - Total deals in context: {len(context_vars.deals_found)}")
    for i, deal in enumerate(context_vars.deals_found):
        print(f"  Deal {i+1}: type={deal.get('type')}, name={deal.get('product_name', deal.get('name', 'N/A'))}")
    
    print(f"Debug - Structured products for frontend: {len(structured_products)}")
    for i, product in enumerate(structured_products[:3]):  # Show first 3
        print(f"  Product {i+1}: {product.get('product_name', 'N/A')} - {product.get('price', 'N/A')}")
    
    return structured_products, messages, final_chat_response


async def process_shopping_query_with_tools_async(
    user_query: str, 
    api_key: str, 
    max_iterations: int = 20
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Async version of process_shopping_query_with_tools that handles async function calls
    """
    import time
    import asyncio
    
    start_time = time.time()
    print(f"🕐 TIMING: Starting async shopping query processing at {time.strftime('%H:%M:%S')}")
    
    counter = 0
    messages = []
    context_vars = ShoppingContextVariables()
    final_chat_response = ""
    
    while counter < max_iterations:
        try:
            turn_start = time.time()
            print(f"🕐 TIMING: Turn {counter + 1} starting at {time.strftime('%H:%M:%S')}")
            
            # Get response from Gemini
            ai_start = time.time()
            response, messages = get_response(
                user_query, messages, api_key, system_prompt=get_system_prompt()
            )
            text = response.choices[0].message.content
            ai_end = time.time()
            print(f"🕐 TIMING: AI response took {ai_end - ai_start:.2f}s")
            
            print(f"DEBUG - AI Response #{counter}: {text}")
            
            # Extract and execute tool call
            tool_call = extract_tool_call_from_response(text)
            print(f"DEBUG - Tool call extracted: {tool_call}")
            
            if tool_call:
                # Execute the tool call (async or sync)
                tool_start = time.time()
                result = await execute_function_with_context_async(
                    tool_call["function_name"], 
                    tool_call["arguments"], 
                    context_vars
                )
                tool_end = time.time()
                print(f"🕐 TIMING: Tool '{tool_call['function_name']}' took {tool_end - tool_start:.2f}s")
                print(f"DEBUG - Tool call result: {result}")
                
                # Check if this was the final chat_message call
                if tool_call["function_name"] == "chat_message" and tool_call["arguments"].get("is_final", False):
                    print(f"DEBUG - Final chat_message called, ending conversation")
                    final_chat_response = context_vars.final_chat_message
                    if not final_chat_response:
                        final_chat_response = "I found some great options for you!"
                    break
                
                # Handle different tool responses
                elif tool_call["function_name"] == "search_product":
                    # After a search, encourage the AI to display products if found
                    if "Found 0 products" in result or "No products found" in result:
                        # No products found - suggest trying different search terms
                        tool_call_message = {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n❌ No products found with current search terms. Try:\n- Broader search terms (remove specific adjectives)\n- Alternative product names or categories\n- Different combinations of keywords\n\nUse search_product again with different terms, or if you've tried multiple searches without success, use chat_message with is_final=true to explain the search challenge."
                        }
                    elif "Found 1 products" in result or "Found 2 products" in result or "Found 3 products" in result:
                        # Very few products found - suggest expanding search
                        tool_call_message = {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n⚠️ Only found {result.split('Found ')[1].split(' products')[0]} products. Consider:\n- Removing price restrictions (increase max_price or remove it)\n- Using broader search terms\n- Trying alternative keywords\n- Searching different marketplaces\n\nUse search_product with expanded criteria to find more options, or display the current results if they meet the user's needs."
                        }
                    else:
                        # Products found - MUST display them immediately
                        tool_call_message = {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n🎉 PRODUCTS FOUND! You MUST now use show_products() to display them to the user immediately.\n\nCreate a curated list of the best products from your search results with:\n- Descriptive product names\n- Clear pricing\n- Store information\n- Helpful badges ('Best Value', 'Premium Choice', etc.)\n- Brief reasoning for each selection\n\nAfter displaying products, you can share reasoning about your findings and end with chat_message (is_final=true)."
                        }
                elif tool_call["function_name"] == "show_products":
                    tool_call_message = {
                        "role": "user", 
                        "content": f"Products displayed successfully: {result}\n\nCall chat_message with is_final=true and a brief, conversational message about what you found to complete the conversation."
                    }
                else:
                    tool_call_message = {
                        "role": "user", 
                        "content": f"Function returned: {result}. Continue your analysis or call chat_message with is_final=true to complete the conversation."
                    }
                
                messages.append(tool_call_message)
            else:
                # No tool call found, prompt for action
                if any(keyword in text.lower() for keyword in ['let me', 'i should', 'i need to', 'i will', 'first', 'then', 'next']):
                    thinking_message = {
                        "role": "user",
                        "content": "Please proceed with your planned action using the appropriate function call."
                    }
                    messages.append(thinking_message)
                else:
                    # No clear next step, break and use current response
                    final_chat_response = text
                    break
            
            counter += 1
            turn_end = time.time()
            print(f"🕐 TIMING: Turn {counter} took {turn_end - turn_start:.2f}s")
            
        except Exception as e:
            print(f"Error in turn {counter}: {str(e)}")
            final_chat_response = f"I encountered an issue while searching: {str(e)}"
            break
    
    # Generate final response if needed
    if not final_chat_response:
        if context_vars.deals_found:
            final_chat_response = "I found some options for you! Take a look at what I discovered."
        else:
            final_chat_response = "I searched for what you're looking for. Let me know if you'd like me to try a different approach!"
    
    # Get structured products for frontend
    structured_products = get_structured_products_json(context_vars)
    
    total_time = time.time() - start_time
    print(f"🕐 TIMING: Total async processing time: {total_time:.2f}s")
    
    return structured_products, messages, final_chat_response


def preprocess_shopping_query(query: str, api_key: str) -> str:
    """
    Preprocess the shopping query to extract key information
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    You are a shopping query preprocessor. Extract the key shopping information from this user query:
    
    Query: {query}
    
    Please extract and return:
    1. Product/item they're looking for
    2. Budget constraints (if mentioned)
    3. Preferred stores/brands (if mentioned)
    4. Specific features or requirements
    5. Any other relevant shopping preferences
    
    Return a clean, structured summary of what the user is looking for.
    """
    
    response = model.generate_content(prompt)
    return response.text 