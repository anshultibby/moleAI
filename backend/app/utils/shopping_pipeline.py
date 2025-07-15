"""
Shopping Pipeline Functions
Core logic for processing shopping queries with tool calling
"""

import google.generativeai as genai
from typing import List, Dict, Any, Tuple
from .gemini_tools_converter import (
    ShoppingContextVariables, 
    execute_function_with_context, 
    extract_tool_call_from_response
)


def get_system_prompt() -> str:
    """Get the system prompt for shopping assistant"""
    return """
You are an expert shopping assistant that helps users find clothing and fashion items. 
You have access to several tools to help with shopping research:

Available functions:
- search_product({"query": "product name", "max_price": number, "category": "category"}) - Search for products on Zara using Firecrawl web scraping. This returns the full page content from Zara's search results, which you should analyze to extract product information including names, prices, availability, and descriptions.
- compare_prices({"product_name": "name", "stores": ["store1", "store2"]}) - Compare prices across stores
- add_deal({"deal_info": {"product_name": "name", "price": "price", "store": "store", "discount": "discount"}}) - Add a deal to results
- get_user_preferences({}) - Get user shopping preferences
- update_preferences({"preferences": {"budget": number, "brands": ["brand1"], "categories": ["cat1"]}}) - Update user preferences

Your goal is to help users find the best clothing and fashion deals by:
1. Understanding their query and preferences
2. Searching for relevant products on Zara using the Firecrawl-powered search
3. Analyzing the returned page content to extract product details
4. Finding the best deals and options
5. Providing helpful recommendations with product details, prices, and availability

When you want to use a function, write it exactly like this:
function_name({"parameter": "value"})

When you're done with your analysis, write "STOP" to finish.

Be conversational and helpful. Always explain what you're doing and why. The search_product function will return full page content from Zara, so you'll need to analyze and extract the relevant product information from the content.
"""


def get_response(
    user_query: str, 
    messages: List[Dict[str, str]], 
    api_key: str, 
    system_prompt: str = None
) -> Tuple[Any, List[Dict[str, str]]]:
    """
    Get response from Gemini with conversation history
    """
    if system_prompt is None:
        system_prompt = get_system_prompt()
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Build conversation history
    conversation_parts = [system_prompt]
    
    # Add message history
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        
        if role == "user":
            conversation_parts.append(f"User: {content}")
        elif role == "assistant":
            conversation_parts.append(f"Assistant: {content}")
    
    # Add current query
    conversation_parts.append(f"User: {user_query}")
    
    # Generate response
    full_prompt = "\n\n".join(conversation_parts)
    response = model.generate_content(full_prompt)
    
    # Update messages
    messages.append({"role": "user", "content": user_query})
    messages.append({"role": "assistant", "content": response.text})
    
    # Mock response object to match your ICD structure
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


def process_shopping_query_with_tools(
    user_query: str, 
    api_key: str, 
    max_iterations: int = 10
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process shopping query with tool calling capability
    Similar to your ICD processing but for shopping
    """
    counter = 0
    messages = []
    context_vars = ShoppingContextVariables()
    
    while counter < max_iterations:
        try:
            # Get response from Gemini
            response, messages = get_response(
                user_query, messages, api_key, system_prompt=get_system_prompt()
            )
            text = response.choices[0].message.content
            
            # Check for stop condition
            if "STOP" in text.upper():
                break
            
            # Extract and execute tool call
            tool_call = extract_tool_call_from_response(text)
            
            if tool_call:
                # Execute the tool call
                result = execute_function_with_context(
                    tool_call["function_name"], 
                    tool_call["arguments"], 
                    context_vars
                )
                
                # Prepare next message
                tool_call_message = {
                    "role": "user", 
                    "content": f"Function returned: {result}. What's your next step?"
                }
                
                # Update messages
                messages.append(tool_call_message)
            else:
                # No tool call found, ask for next step
                no_tool_message = {
                    "role": "user", 
                    "content": "No function call found. What's your next step?"
                }
                messages.append(no_tool_message)
            
            counter += 1
            
        except Exception as e:
            print(f"Error in shopping query processing: {str(e)}")
            break
    
    return context_vars.deals_found, messages


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