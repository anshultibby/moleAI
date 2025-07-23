"""
Streaming Agent Implementation
Integrates with the existing streaming pipeline to provide real-time agentic loop updates
"""

import asyncio
import time
from typing import AsyncGenerator, Dict, Any, List, Optional
from .agent import Agent, Tool, LLM, ToolCall


class StreamingAgent(Agent):
    """
    Streaming version of Agent that yields real-time updates during conversation
    Compatible with the existing frontend streaming interface
    """
    
    def __init__(self, name: str, description: str, tools: List[Tool], llm: LLM):
        super().__init__(name, description, tools, llm)
        self.conversation_id = None
    
    async def run_conversation_streaming(
        self, 
        user_message: str, 
        max_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the agentic conversation loop with streaming updates
        Yields updates compatible with the existing frontend streaming format
        """
        conversation = []
        self.conversation_id = f"conv_{int(time.time())}"
        
        # Yield start signal
        yield {
            "type": "start",
            "message": f"Starting conversation with {self.name}",
            "conversation_id": self.conversation_id
        }
        
        # Add user message
        conversation.append({
            'role': 'user',
            'content': user_message,
            'type': 'message'
        })
        
        # Yield user message
        yield {
            "type": "message",
            "data": {
                "role": "user",
                "content": user_message,
                "timestamp": time.time()
            }
        }
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Yield thinking status
            yield {
                "type": "thinking",
                "data": {
                    "message": f"Processing... (iteration {iteration})",
                    "iteration": iteration
                }
            }
            
            # Get LLM response
            try:
                llm_response = await self._get_llm_response_async([
                    {k: v for k, v in msg.items() if k in ['role', 'content']} 
                    for msg in conversation
                ])
            except Exception as e:
                yield {
                    "type": "error",
                    "message": f"Error getting LLM response: {str(e)}"
                }
                return
            
            # Check if this is a tool call or assistant message
            tool_call = self._extract_tool_call(llm_response)
            
            if tool_call:
                # Add tool call to conversation
                conversation.append({
                    'role': 'assistant',
                    'content': llm_response,
                    'type': 'tool_call',
                    'tool_call': {
                        'name': tool_call.name,
                        'arguments': tool_call.arguments,
                        'call_id': tool_call.call_id
                    }
                })
                
                # Yield tool call update
                yield {
                    "type": "tool_call",
                    "data": {
                        "tool_name": tool_call.name,
                        "arguments": tool_call.arguments,
                        "call_id": tool_call.call_id,
                        "timestamp": time.time()
                    }
                }
                
                # Execute the tool
                if tool_call.name in self.tools:
                    tool = self.tools[tool_call.name]
                    
                    # Yield tool execution start
                    yield {
                        "type": "tool_execution",
                        "data": {
                            "status": "executing",
                            "tool_name": tool_call.name,
                            "message": f"Executing {tool_call.name}..."
                        }
                    }
                    
                    try:
                        # For search_product, we need to monitor the streaming queue during execution
                        if tool_call.name == "search_product":
                            # Clear the queue before execution
                            from ..utils.streaming_service import get_streaming_service
                            streaming_service = get_streaming_service()
                            streaming_service.clear_queue()
                            
                            # Execute tool and monitor queue
                            result = await self._execute_tool_async(tool, tool_call.arguments)
                            
                            # Stream any products that were queued during execution
                            queued_products = streaming_service.get_queued_products()
                            for product_update in queued_products:
                                yield product_update
                        else:
                            result = await self._execute_tool_async(tool, tool_call.arguments)
                        
                        # Add tool result to conversation
                        conversation.append({
                            'role': 'function',
                            'content': result,
                            'type': 'tool_result',
                            'tool_call_id': tool_call.call_id,
                            'tool_name': tool_call.name
                        })
                        
                        # Yield tool result for non-search tools
                        if tool_call.name != "search_product":
                            yield {
                                "type": "tool_result",
                                "data": {
                                    "tool_name": tool_call.name,
                                    "result": result,
                                    "call_id": tool_call.call_id,
                                    "timestamp": time.time()
                                }
                            }
                        
                    except Exception as e:
                        error_msg = f"Error executing {tool_call.name}: {str(e)}"
                        conversation.append({
                            'role': 'function',
                            'content': error_msg,
                            'type': 'tool_result',
                            'tool_call_id': tool_call.call_id,
                            'tool_name': tool_call.name
                        })
                        
                        yield {
                            "type": "tool_error",
                            "data": {
                                "tool_name": tool_call.name,
                                "error": error_msg,
                                "call_id": tool_call.call_id,
                                "timestamp": time.time()
                            }
                        }
                else:
                    # Tool not found
                    error_msg = f"Error: Tool '{tool_call.name}' not found"
                    conversation.append({
                        'role': 'function',
                        'content': error_msg,
                        'type': 'tool_result',
                        'tool_call_id': tool_call.call_id,
                        'tool_name': tool_call.name
                    })
                    
                    yield {
                        "type": "tool_error",
                        "data": {
                            "tool_name": tool_call.name,
                            "error": error_msg,
                            "call_id": tool_call.call_id,
                            "timestamp": time.time()
                        }
                    }
                
                # Continue the loop to get next response
                continue
            else:
                # This is a regular assistant message - conversation ends
                conversation.append({
                    'role': 'assistant',
                    'content': llm_response,
                    'type': 'message'
                })
                
                # Yield final assistant message
                yield {
                    "type": "message",
                    "data": {
                        "role": "assistant",
                        "content": llm_response,
                        "timestamp": time.time(),
                        "is_final": True
                    }
                }
                break
        
        # Yield completion
        yield {
            "type": "complete",
            "data": {
                "conversation_id": self.conversation_id,
                "total_iterations": iteration,
                "final_conversation": conversation
            }
        }
    
    async def _get_llm_response_async(self, messages: List[Dict[str, str]]) -> str:
        """Get LLM response asynchronously"""
        # Run the synchronous LLM call in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_chat_completion, messages)
    
    async def _execute_tool_async(self, tool: Tool, arguments: Dict[str, Any]) -> str:
        """Execute tool asynchronously"""
        # Run the tool execution in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, tool.call, **arguments)


def create_agent_from_existing_tools() -> StreamingAgent:
    """
    Create a streaming agent using the existing tool functions from the codebase
    This bridges the new agent system with the existing shopping tools
    """
    from ..utils.gemini_tools_converter import execute_function_with_context, ShoppingContextVariables
    
    # Create a wrapper for existing shopping tools with streaming support
    def search_product_wrapper(**kwargs):
        context = ShoppingContextVariables()
        result = execute_function_with_context("search_product", kwargs, context)
        
        # The search_product function adds products to context.deals_found
        # We need to stream these products individually
        from ..utils.streaming_service import get_streaming_service
        streaming_service = get_streaming_service()
        
        # Stream each product found
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
        
        # Stream the final chat message
        from ..utils.streaming_service import get_streaming_service
        streaming_service = get_streaming_service()
        
        message = kwargs.get('message', result)
        streaming_service.queue_product_update({
            "type": "chat_response", 
            "message": message,
            "data": {"is_final": kwargs.get('is_final', True)}
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
            },
            "category": {
                "type": "string", 
                "description": "Product category filter",
                "required": False
            },
            "marketplaces": {
                "type": "array",
                "description": "List of marketplaces to search (default: ['SHOPIFY'])",
                "required": False
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of products to return (default: 50)",
                "required": False
            }
        }
    )
    
    chat_tool = Tool(
        name="chat_message",
        description="Send a final conversational message to the user",
        function=chat_message_wrapper,
        parameters={
            "message": {
                "type": "string",
                "description": "The message to send to the user",
                "required": True
            },
            "tone": {
                "type": "string",
                "description": "The tone of the message (excited, helpful, etc.)",
                "required": False
            },
            "is_final": {
                "type": "boolean",
                "description": "Whether this is the final message (default: true)",
                "required": False
            }
        }
    )
    
    # Create LLM with centralized config
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    llm = LLM(model_name="gemini-2.0-flash-exp", api_key=GEMINI_API_KEY)
    
    # Create the streaming agent
    agent = StreamingAgent(
        name="Shopping Assistant",
        description="An expert shopping assistant that can search for products and provide helpful recommendations",
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