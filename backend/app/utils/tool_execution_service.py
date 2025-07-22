"""
Tool Execution Service
Handles execution of AI function calls with streaming support
"""

import time
from typing import Dict, Any, Optional
from .gemini_tools_converter import (
    ShoppingContextVariables, 
    execute_function_with_context,
    extract_tool_call_from_response
)
from .streaming_service import get_streaming_service


class ToolExecutionService:
    """Manages execution of AI function calls with streaming support"""
    
    def __init__(self):
        self.streaming_service = get_streaming_service()
    
    def extract_tool_call(self, ai_response: str) -> Optional[Dict[str, Any]]:
        """Extract tool call from AI response"""
        return extract_tool_call_from_response(ai_response)
    
    def execute_tool_with_streaming(
        self, 
        tool_call: Dict[str, Any], 
        context_vars: ShoppingContextVariables
    ) -> str:
        """Execute a tool call and stream any products found during execution"""
        
        function_name = tool_call["function_name"]
        arguments = tool_call["arguments"]
        
        print(f"🔧 TOOL: Executing {function_name}")
        print(f"   🔧 Queue size before execution: {self.streaming_service.get_queue_size()}")
        
        # Execute the tool call
        tool_start = time.time()
        result = execute_function_with_context(function_name, arguments, context_vars)
        tool_end = time.time()
        
        print(f"   🔧 Queue size after execution: {self.streaming_service.get_queue_size()}")
        print(f"🕐 TIMING: Tool '{function_name}' took {tool_end - tool_start:.2f}s")
        
        return result
    
    def get_products_from_queue(self) -> list:
        """Get all queued products for streaming"""
        return self.streaming_service.get_queued_products()
    
    def process_tool_result(
        self, 
        tool_call: Dict[str, Any], 
        result: str,
        context_vars: ShoppingContextVariables
    ) -> Dict[str, Any]:
        """Process tool execution result and provide guidance for next steps"""
        
        function_name = tool_call["function_name"]
        
        # Handle different function types
        if function_name == "search_product":
            return self._handle_search_result(result, tool_call["arguments"])
        elif function_name == "show_products":
            return self._handle_show_products_result(result)
        elif function_name == "chat_message":
            return self._handle_chat_message_result(result, tool_call["arguments"])
        else:
            return self._handle_generic_result(result)
    
    def _handle_search_result(self, result: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search_product tool result"""
        
        if "Found 0 products" in result or "No products found" in result:
            return {
                "should_continue": True,
                "next_message": {
                    "role": "user", 
                    "content": f"Search completed: {result}\n\n❌ No products found with current search terms. Try ONE more relevant approach:\n\n🔄 NEXT STEPS:\n1. Try slightly BROADER but still relevant terms (e.g., if 'black leather jacket' found nothing, try 'leather jacket')\n2. Try ALTERNATIVE but related product names\n3. Consider slight price range adjustment if budget was very restrictive\n\n🎯 FOCUS ON RELEVANCE: Only try variations that would still match what the user actually wants. Better to show fewer highly relevant results than many loosely related ones.\n\nUse search_product ONE more time with a relevant variation, or use chat_message with is_final=true to explain the specific search challenge."
                }
            }
        
        # Extract product count
        try:
            if "Found " in result and " products" in result:
                product_count = int(result.split('Found ')[1].split(' products')[0])
                
                if product_count <= 5:
                    return {
                        "should_continue": True,
                        "next_message": {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n⚠️ Only found {product_count} products - NOT ENOUGH! You need products from at least 8-15 different websites/domains for a good selection.\n\n🔄 REQUIRED ACTIONS:\n1. Try BROADER search terms (remove specific details)\n2. INCREASE max_price or remove price restrictions entirely\n3. Try ALTERNATIVE keywords and product names\n4. Search for RELATED product categories\n5. Try DIFFERENT marketplace combinations\n\n🎯 KEEP SEARCHING until you have products from 8-15+ different websites. Use search_product again with expanded criteria!"
                        }
                    }
                elif product_count <= 10:
                    return {
                        "should_continue": True,
                        "next_message": {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n⚡ Found {product_count} products - getting better but still need more variety from different websites! Try ONE MORE broader search to reach products from 15+ different domains.\n\n🔄 SUGGESTED IMPROVEMENTS:\n1. Remove specific adjectives or requirements\n2. Increase price range significantly\n3. Try more general product category terms\n4. Search without brand restrictions\n\nAfter this next search, you should have enough products from various websites to display a good selection. Use search_product with broader terms, then show_products() to display all results."
                        }
                    }
                else:
                    # Good number of products found
                    return {
                        "should_continue": True,
                        "next_message": {
                            "role": "user", 
                            "content": f"Search completed: {result}\n\n🎉 GREAT! You found a good selection of products! You MUST now use show_products() to display them to the user immediately.\n\nCreate a curated list of the best products from your search results with:\n- Descriptive product names\n- Clear pricing\n- Store information\n- Helpful badges ('Best Value', 'Premium Choice', etc.)\n- Brief reasoning for each selection\n\nAfter displaying products, you can share reasoning about your findings and end with chat_message (is_final=true)."
                        }
                    }
        except (ValueError, IndexError):
            pass
        
        # Default case - products found
        return {
            "should_continue": True,
            "next_message": {
                "role": "user", 
                "content": f"Search completed: {result}\n\nProducts found! Please use show_products() to display them to the user, then complete with chat_message (is_final=true)."
            }
        }
    
    def _handle_show_products_result(self, result: str) -> Dict[str, Any]:
        """Handle show_products tool result"""
        return {
            "should_continue": True,
            "next_message": {
                "role": "user", 
                "content": f"Products displayed successfully: {result}\n\nYou now have product data displayed to the user. Call chat_message with is_final=true and a brief, conversational message about what you found to complete the conversation."
            }
        }
    
    def _handle_chat_message_result(self, result: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat_message tool result"""
        is_final = arguments.get("is_final", False)
        
        return {
            "should_continue": not is_final,
            "is_final": is_final,
            "next_message": None
        }
    
    def _handle_generic_result(self, result: str) -> Dict[str, Any]:
        """Handle generic tool result"""
        return {
            "should_continue": True,
            "next_message": {
                "role": "user", 
                "content": f"Function returned: {result}. Continue your analysis or call chat_message with is_final=true to complete the conversation."
            }
        }


# Global instance
_tool_execution_service = ToolExecutionService()


def get_tool_execution_service() -> ToolExecutionService:
    """Get the global tool execution service"""
    return _tool_execution_service 