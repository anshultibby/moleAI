from typing import List, Optional, Generator, Dict, Any, Callable
from openai import OpenAI
import json
from loguru import logger
from app.models.chat import (
    ToolCall, 
    ToolCallOutput, 
    Message, 
    InputMessage,
    ThinkingResponse,
    ToolCallsResponse,
    AssistantResponse,
    AgentResponse,
    OpenAIResponse,
    ResponseReasoningItem,
    ResponseOutputMessage,
)
from app.models.resource import Resource
from app.tools import tool_registry


class Agent:
    def __init__(self, 
                 system_prompt: str, 
                 model: str, 
                 reasoning_effort: str = "medium",
                 api_key: Optional[str] = None):
        self.system_prompt = system_prompt
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.message_history: List[InputMessage] = []
        self.client = OpenAI(api_key=api_key)
        
        # Initialize resource storage
        self.resources: Dict[str, Resource] = {}
        
        # Define context variables that will be available to tools
        self.context_vars = {
            'resources': self.resources,
            'conversation_id': getattr(self, 'conversation_id', None)
        }
        
        # Always use registry tools
        self.tools = tool_registry.to_openai_format()
        
        # Add system message to history
        system_message = Message(
            role="system", 
            content=self.system_prompt
        )
        self.message_history.append(system_message)

    def step(self, input_message: InputMessage) -> OpenAIResponse:
        """Add an input message and call the OpenAI responses API"""
        if input_message is not None:
            self.message_history.append(input_message)
            
            # Log what we're sending to OpenAI
            if hasattr(input_message, 'content') and input_message.content:
                logger.info(f"→ Sending {input_message.role}: {input_message.content[:200]}{'...' if len(input_message.content) > 200 else ''}")
            else:
                logger.info(f"→ Sending {input_message.role} message")
        else:
            logger.info("→ Continuing conversation after tool execution")
        
        # Clean up any None values that might have accumulated
        self.clean_message_history()
        
        # Convert models to dict format for API call
        input_data = []
        for i, msg in enumerate(self.message_history):
            if msg is not None:
                input_data.append(msg.dict())
            else:
                logger.warning(f"Skipping None message at index {i}")
        
        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "input": input_data
        }
        
        if self.tools:
            api_params["tools"] = [tool.dict() for tool in self.tools]
            
        if self.reasoning_effort:
            api_params["reasoning"] = {"effort": self.reasoning_effort}
        
        # Call OpenAI responses API
        raw_response = self.client.responses.create(**api_params)
        
        # Parse response using Pydantic model for type safety
        try:
            response = OpenAIResponse.parse_obj(raw_response.dict())
            # Log what OpenAI returned with content
            logger.info(f"← OpenAI response ({len(response.output)} items):")
            for i, output_item in enumerate(response.output):
                if isinstance(output_item, ResponseReasoningItem):
                    # Handle reasoning items specially to show their content
                    # Debug: Print the raw reasoning object structure
                    logger.debug(f"Raw reasoning object: {output_item.dict()}")
                    
                    reasoning_parts = []
                    if output_item.content:
                        reasoning_parts.append(f"content: {output_item.content[:300]}{'...' if len(output_item.content) > 300 else ''}")
                    if output_item.encrypted_content:
                        reasoning_parts.append(f"encrypted_content: [encrypted]")
                    if output_item.summary:
                        summary_text = " | ".join(output_item.summary)
                        reasoning_parts.append(f"summary: {summary_text[:200]}{'...' if len(summary_text) > 200 else ''}")
                    
                    reasoning_display = " | ".join(reasoning_parts) if reasoning_parts else "[no content]"
                    logger.info(f"  [{i+1}] reasoning: {reasoning_display}")
                    
                    # Additional debug info
                    logger.debug(f"Reasoning fields - content: {bool(output_item.content)}, encrypted_content: {bool(output_item.encrypted_content)}, summary: {bool(output_item.summary)}, status: {output_item.status}")
                elif hasattr(output_item, 'content') and output_item.content:
                    logger.info(f"  [{i+1}] {output_item.type if hasattr(output_item, 'type') else 'message'}: {output_item.content[:200]}{'...' if len(output_item.content) > 200 else ''}")
                elif hasattr(output_item, 'name'):
                    logger.info(f"  [{i+1}] function_call: {output_item.name}({output_item.arguments if hasattr(output_item, 'arguments') else ''})")
                else:
                    logger.info(f"  [{i+1}] {type(output_item).__name__}")
            return response
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            # Return raw response as fallback
            return raw_response
        
    
    def add_to_history(self, message: InputMessage):
        """Add a message to the conversation history"""
        if message is None:
            logger.error("Attempted to add None message to history")
            return
        self.message_history.append(message)
        
        # Log tool results being sent
        if hasattr(message, 'output') and message.output:
            logger.info(f"→ Sending tool result: {message.output}")
        elif hasattr(message, 'role') and message.role == 'tool':
            logger.info(f"→ Sending tool message")
    
    def clean_message_history(self):
        """Remove any None values from message history"""
        original_length = len(self.message_history)
        self.message_history = [msg for msg in self.message_history if msg is not None]
        cleaned_count = original_length - len(self.message_history)
        if cleaned_count > 0:
            logger.warning(f"Removed {cleaned_count} None messages from history")
    
    
    def execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a tool call using the tool registry"""
        if not tool_registry.has_tool(tool_call.name):
            return f"Error: Tool '{tool_call.name}' not found in registry"
        
        try:
            # Parse arguments and execute using registry
            args = tool_call.parse_arguments()
            
            # Use agent's context variables for tool execution
            result = tool_registry.execute_tool(tool_call.name, context_vars=self.context_vars, **args)
            
            # Store the raw result for special handling
            self._last_tool_result = {
                'tool_name': tool_call.name,
                'result': result
            }
            
            # OpenAI API requires string output, but we store the original for special handling
            return str(result)
        except Exception as e:
            return f"Error executing {tool_call.name}: {str(e)}"
    
    def run(self, initial_message: InputMessage) -> Generator[AgentResponse, InputMessage, None]:
        """
        Run the conversation loop. Yields responses and waits for user input.
        
        Yields:
        - Assistant responses when conversation stops
        - Tool call information when tools are being executed
        
        Sends:
        - User input messages to continue the conversation
        """
        current_message = initial_message
        
        while True:
            # Call OpenAI API
            response = self.step(current_message)
            
            # First, yield any thinking/reasoning content
            for output_item in response.output:
                if isinstance(output_item, ResponseReasoningItem):
                    # Handle reasoning content extraction with type safety
                    reasoning_content = []
                    reasoning_summary = None
                    
                    # Try to extract content from various possible fields
                    if output_item.content:
                        reasoning_content = [output_item.content]
                    elif output_item.encrypted_content:
                        # Handle encrypted content if available
                        reasoning_content = [f"[Encrypted reasoning content available but not accessible]"]
                    
                    # Extract summary if available
                    if output_item.summary:
                        reasoning_summary = output_item.summary
                    
                    # Only yield if we have some content or summary
                    if reasoning_content or reasoning_summary:
                        yield ThinkingResponse(
                            content=reasoning_content,
                            summary=reasoning_summary,
                            response=response
                        )
            
            # Check if response has tool calls or assistant messages
            has_tool_calls = False
            has_assistant_message = False
            tool_calls = []
            tool_outputs = []
            raw_tool_results = {}  # Store original structured results
            
            # First, add all reasoning items to history to maintain OpenAI's required structure
            reasoning_items = []
            for output_item in response.output:
                if isinstance(output_item, ResponseReasoningItem):
                    reasoning_items.append(output_item)
                    # Add reasoning items to history as they are required by OpenAI
                    input_item = output_item.to_input_format()
                    self.add_to_history(input_item)
            
            # Then process function calls
            for output_item in response.output:
                if hasattr(output_item, 'type') and output_item.type == "function_call":
                    has_tool_calls = True
                    
                    # Create ToolCall object
                    tool_call = ToolCall(
                        id=output_item.id,
                        call_id=output_item.call_id,
                        name=output_item.name,
                        arguments=output_item.arguments
                    )
                    
                    # Execute the tool call
                    result = self.execute_tool_call(tool_call)
                    
                    # Store raw result for special handling (before string conversion)
                    if hasattr(self, '_last_tool_result') and self._last_tool_result:
                        raw_tool_results[tool_call.call_id] = self._last_tool_result['result']
                    
                    # Create tool call output
                    tool_output = ToolCallOutput(
                        call_id=tool_call.call_id,
                        output=result
                    )
                    
                    # Add the function call item to history (not individual ToolCall/ToolCallOutput)
                    input_item = output_item.to_input_format()
                    self.add_to_history(input_item)
                    self.add_to_history(tool_output)
                    
                    # Collect both calls and outputs
                    tool_calls.append(tool_call)
                    tool_outputs.append(tool_output)
                    
                elif isinstance(output_item, ResponseOutputMessage):
                    has_assistant_message = True
            
            if has_tool_calls:
                # Yield both tool calls and their results
                yield ToolCallsResponse(
                    tool_calls=tool_calls,
                    tool_outputs=tool_outputs,
                    response=response,
                    raw_tool_results=raw_tool_results
                )
                
                # Continue with empty message to get next response
                current_message = None
                
            elif has_assistant_message:
                # Has assistant message - yield the response and wait for user input
                yield AssistantResponse(response=response)
                
                # Wait for next user input
                current_message = yield
                
                if current_message is None:
                    break
            else:
                # No tool calls or assistant messages - this shouldn't happen normally
                logger.warning(f"Response has no tool calls or assistant messages: {response}")
                yield AssistantResponse(response=response)
                
                # Wait for next user input
                current_message = yield
                
                if current_message is None:
                    break
    
    def get_message_history(self) -> List[InputMessage]:
        return self.message_history.copy()
    
    def get_system_prompt(self) -> str:
        return self.system_prompt
    