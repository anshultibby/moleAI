"""
Clean Streaming Pipeline
Uses dedicated services for streaming and tool execution
"""

import time
from typing import AsyncGenerator, Dict, Any, List
from .gemini_response_service import get_gemini_response
from .streaming_service import get_streaming_service
from .tool_execution_service import get_tool_execution_service
from .gemini_tools_converter import ShoppingContextVariables, get_structured_products_json
from .progress_utils import get_and_clear_progress_messages



async def process_shopping_query_streaming(
    user_query: str, 
    api_key: str, 
    max_iterations: int = 20
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Clean streaming pipeline with real-time product streaming during tool execution
    """
    import asyncio
    import concurrent.futures
    
    start_time = time.time()
    print(f"🕐 STREAMING: Starting at {time.strftime('%H:%M:%S')}")
    
    # Initialize services
    streaming_service = get_streaming_service()
    tool_service = get_tool_execution_service()
    
    # Set up streaming callback
    streaming_callback = streaming_service.create_streaming_callback()
    streaming_service.set_streaming_callback(streaming_callback)
    
    # Initialize conversation state
    counter = 0
    messages = []
    context_vars = ShoppingContextVariables()
    final_chat_response = ""
    
    while counter < max_iterations:
        try:
            turn_start = time.time()
            print(f"🕐 TURN {counter + 1}: Starting at {time.strftime('%H:%M:%S')}")
            
            # Yield any queued products first
            queued_products = streaming_service.get_queued_products()
            for product_update in queued_products:
                print(f"   🎯 YIELDING: {product_update['data'].get('product_name', 'Unknown')}")
                yield product_update
            
            # Get AI response
            ai_start = time.time()
            response, messages = get_gemini_response(
                user_query, messages, api_key
            )
            ai_response_text = response.choices[0].message.content
            ai_end = time.time()
            print(f"🕐 AI response: {ai_end - ai_start:.2f}s")
            
            # Extract and execute tool call
            tool_call = tool_service.extract_tool_call(ai_response_text)
            print(f"🔧 Tool call: {tool_call['function_name'] if tool_call else 'None'}")
            
            if tool_call:
                # For long-running tools like search_product, execute in thread pool and stream concurrently
                if tool_call["function_name"] == "search_product":
                    print(f"   🚀 Starting long-running tool execution with concurrent streaming...")
                    
                    # Execute tool in a thread pool to avoid blocking
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            tool_service.execute_tool_with_streaming, 
                            tool_call, 
                            context_vars
                        )
                        
                        # While tool is executing, continuously stream products
                        while not future.done():
                            # Check for new products every 500ms
                            await asyncio.sleep(0.5)
                            
                            # Yield any products that have been queued
                            new_products = streaming_service.get_queued_products()
                            for product_update in new_products:
                                print(f"   🚀 LIVE STREAM: {product_update['data'].get('product_name', 'Unknown')}")
                                yield product_update
                        
                        # Get the final result
                        result = future.result()
                        print(f"   ✅ Tool execution completed: {result}")
                
                else:
                    # For fast tools, execute normally
                    result = tool_service.execute_tool_with_streaming(tool_call, context_vars)
                
                # Yield any final products that were discovered
                final_products = tool_service.get_products_from_queue()
                for product_update in final_products:
                    print(f"   🎯 FINAL: {product_update['data'].get('product_name', 'Unknown')}")
                    yield product_update
                
                # Process tool result for next steps
                processing_result = tool_service.process_tool_result(tool_call, result, context_vars)
                
                # Check if this was the final message
                if processing_result.get("is_final", False):
                    final_chat_response = context_vars.final_chat_message or "Search completed!"
                    yield {"type": "chat_response", "message": final_chat_response}
                    break
                
                # Add guidance message for next iteration
                if processing_result.get("next_message"):
                    messages.append(processing_result["next_message"])
                
                # Stop if we shouldn't continue
                if not processing_result.get("should_continue", True):
                    break
            
            else:
                # No tool call - handle thinking/planning
                if any(keyword in ai_response_text.lower() for keyword in ['let me', 'i should', 'i need to', 'i will']):
                    messages.append({
                        "role": "user",
                        "content": "Please proceed with your planned action using the appropriate function call."
                    })
                else:
                    # No clear action, provide guidance
                    messages.append({
                        "role": "user", 
                        "content": "No function call detected. If you need more information, use search_product. If you have sufficient information, use show_products to display your results. If you have products displayed, use chat_message with is_final=true to complete the conversation."
                    })
            
            counter += 1
            turn_end = time.time()
            print(f"🕐 TURN {counter}: Completed in {turn_end - turn_start:.2f}s")
            
        except Exception as e:
            print(f"❌ Error in turn {counter}: {e}")
            yield {"type": "error", "message": str(e)}
            break
    
    # Yield any final queued products
    final_products = streaming_service.get_queued_products()
    for product_update in final_products:
        print(f"   🎯 FINAL: {product_update['data'].get('product_name', 'Unknown')}")
        yield product_update
    
    # Final timing and stats
    total_time = time.time() - start_time
    stats = streaming_service.get_stats()
    print(f"🕐 TOTAL: {total_time:.2f}s, {counter} turns")
    print(f"📊 STATS: {stats['products_queued']} queued, {stats['products_yielded']} yielded")
    
    # Generate final response if needed
    if not final_chat_response:
        if context_vars.deals_found:
            final_chat_response = "I found some great options for you!"
        else:
            final_chat_response = "I searched for what you're looking for. Let me know if you'd like me to try a different approach!"
        
        yield {"type": "chat_response", "message": final_chat_response} 