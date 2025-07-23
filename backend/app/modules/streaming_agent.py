"""
Streaming Agent Implementation
Integrates with the existing streaming pipeline to provide real-time agentic loop updates
"""

import asyncio
import time
from typing import AsyncGenerator, Dict, Any, List
from .agent import Agent, Tool, LLM, ToolCall, ToolCallList

class StreamingAgent(Agent):
    """
    Streaming version of Agent that yields real-time updates during conversation
    Compatible with the existing frontend streaming interface
    """
    
    def __init__(self, name: str, description: str, tools: List[Tool], llm: LLM):
        super().__init__(name, description, tools, llm)
        self.conversation_id = None
    
    async def _execute_tool_calls_streaming(
        self, 
        response: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Extract and execute tool calls with streaming updates
        """
        try:
            if "```json" in response:
                # Extract JSON from code block
                parts = response.split("```")
                for part in parts:
                    if part.strip().startswith("json"):
                        json_str = part.replace("json", "").strip()
                        tool_calls = ToolCallList.model_validate_json(json_str)
                        
                        # Yield the tool calls response
                        yield {
                            "type": "tool_calls",
                            "data": {
                                "content": response,
                                "timestamp": time.time()
                            }
                        }
                        
                        # Execute each tool in sequence
                        for tool_call in tool_calls.tool_calls:
                            if tool_call.name in self.tools:
                                tool = self.tools[tool_call.name]
                                
                                # Yield tool call start
                                yield {
                                    "type": "tool_call",
                                    "data": {
                                        "tool_name": tool_call.name,
                                        "arguments": tool_call.arguments,
                                        "timestamp": time.time()
                                    }
                                }
                                
                                # Special handling for search_product
                                if tool_call.name == "search_product":
                                    # Clear streaming queue
                                    from ..utils.streaming_service import get_streaming_service
                                    streaming_service = get_streaming_service()
                                    streaming_service.clear_queue()
                                    
                                    # Execute tool
                                    result = await self._execute_tool_async(tool, tool_call.arguments)
                                    
                                    # Stream queued products
                                    for product in streaming_service.get_queued_products():
                                        yield product
                                else:
                                    # Execute regular tool
                                    result = await self._execute_tool_async(tool, tool_call.arguments)
                                    
                                    # Yield tool result
                                    yield {
                                        "type": "tool_result",
                                        "data": {
                                            "tool_name": tool_call.name,
                                            "result": result,
                                            "timestamp": time.time()
                                        }
                                    }
                                
                                # Add result to messages
                                yield {
                                    "type": "function",
                                    "data": {
                                        "content": result,
                                        "timestamp": time.time()
                                    }
                                }
                        
                        return
        except:
            pass
        
        # If no tool calls or error, yield as regular message
        yield {
            "type": "message",
            "data": {
                "role": "assistant",
                "content": response,
                "timestamp": time.time(),
                "is_final": True
            }
        }
    
    async def run_conversation_streaming(
        self, 
        user_message: str, 
        max_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the agentic conversation loop with streaming updates
        Yields updates compatible with the existing frontend streaming format
        """
        self.conversation_id = f"conv_{int(time.time())}"
        
        # Initialize messages with system instructions
        messages = [
            {"role": "system", "content": self.system_instructions},
            {"role": "user", "content": user_message}
        ]
        
        # Yield start signal
        yield {
            "type": "start",
            "message": f"Starting conversation with {self.name}",
            "conversation_id": self.conversation_id
        }
        
        # Yield user message
        yield {
            "type": "message",
            "data": {
                "role": "user",
                "content": user_message,
                "timestamp": time.time()
            }
        }
        
        for _ in range(max_iterations):
            # Yield thinking status
            yield {
                "type": "thinking",
                "data": {
                    "message": "Processing...",
                    "iteration": _
                }
            }
            
            try:
                # Get LLM response
                response = await self._get_llm_response_async(messages)
                
                # Process and stream tool calls
                async for update in self._execute_tool_calls_streaming(response):
                    yield update
                    if "data" in update:
                        # Add to conversation history
                        if update["type"] in ["message", "tool_calls", "function"]:
                            messages.append({
                                "role": "assistant" if update["type"] != "function" else "function",
                                "content": update["data"].get("content", "")
                            })
                
                # If tool calls were executed, continue the conversation
                if "```json" in response:
                    continue
                    
                break
                
            except Exception as e:
                yield {
                    "type": "error",
                    "message": f"Error: {str(e)}"
                }
                return
        
        # Yield completion
        yield {
            "type": "complete",
            "data": {
                "conversation_id": self.conversation_id,
                "total_iterations": _,
                "messages": messages
            }
        }
    
    async def _get_llm_response_async(self, messages: List[Dict[str, str]]) -> str:
        """Get LLM response asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.llm.chat_completion, messages)
    
    async def _execute_tool_async(self, tool: Tool, arguments: Dict[str, Any]) -> str:
        """Execute tool asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, tool.call, **arguments)

def create_agent_from_existing_tools() -> StreamingAgent:
    """Create a streaming agent using the existing tool functions"""
    from ..utils.gemini_tools_converter import execute_function_with_context, ShoppingContextVariables
    
    # Create a wrapper for existing shopping tools with streaming support
    def search_product_wrapper(**kwargs):
        context = ShoppingContextVariables()
        result = execute_function_with_context("search_product", kwargs, context)
        
        # Stream products found
        from ..utils.streaming_service import get_streaming_service
        streaming_service = get_streaming_service()
        
        for deal in context.deals_found:
            if deal.get('type') == 'product':
                streaming_service.queue_product_update({
                    "type": "product",
                    "data": deal
                })
        
        return result
    
    def chat_message_wrapper(**kwargs):
        context = ShoppingContextVariables()
        result = execute_function_with_context("chat_message", kwargs, context)
        
        # Stream chat message
        from ..utils.streaming_service import get_streaming_service
        streaming_service = get_streaming_service()
        
        message = kwargs.get('message', result)
        streaming_service.queue_product_update({
            "type": "chat_response", 
            "message": message,
            "timestamp": time.time()
        })
        
        return result
    
    # Define tools using existing functions
    search_tool = Tool(
        name="search_product",
        description="Search for products across multiple stores using our Shopify JSON system",
        function=search_product_wrapper,
        parameters={
            "query": {
                "type": "string",
                "description": "Product search query (e.g., 'winter coat', 'wireless headphones')",
                "required": True
            },
            "max_price": {
                "type": "number",
                "description": "Maximum price filter",
                "required": False
            }
        }
    )
    
    chat_tool = Tool(
        name="chat_message",
        description="Send a chat message to the user",
        function=chat_message_wrapper,
        parameters={
            "message": {
                "type": "string",
                "description": "Message to send to user",
                "required": True
            }
        }
    )
    
    # Create LLM
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")
    
    llm = LLM(
        model_name="gemini-2.0-flash-exp",
        api_key=GEMINI_API_KEY
    )
    
    # Create agent
    agent = StreamingAgent(
        name="Shopping Assistant",
        description="A helpful assistant that can search for products and chat with users",
        tools=[search_tool, chat_tool],
        llm=llm
    )
    
    return agent


async def process_query_with_streaming_agent(user_query: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Process a user query using the streaming agent
    This function can be called directly from the chat route
    """
    try:
        agent = create_agent_from_existing_tools()
        async for update in agent.run_conversation_streaming(user_query):
            yield update
    except Exception as e:
        yield {
            "type": "error",
            "message": f"Error in streaming agent: {str(e)}"
        } 