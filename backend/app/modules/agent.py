from typing import List, Optional, Generator, Dict, Any, Callable
import json
from datetime import datetime
from loguru import logger
from app.models.chat import (
    ToolCall, 
    ToolCallOutput, 
    Message, 
    InputMessage,
    ThinkingResponse,
    ToolCallsResponse,
    AssistantResponse,
    ToolExecutionResponse,
    AgentResponse,
    OpenAIResponse,
    ResponseReasoningItem,
    ResponseOutputMessage,
)
from app.models.resource import Resource
from app.tools import tool_registry
from app.utils.chat_storage import chat_storage
from app.llm.router import LLMRouter


class Agent:
    def __init__(self, 
                 system_prompt: str, 
                 model: str, 
                 reasoning_effort: str = "medium",
                 llm_router: Optional[LLMRouter] = None,
                 stream_callback: Optional[Callable[[ToolExecutionResponse], None]] = None,
                 conversation_id: Optional[str] = None):
        self.system_prompt = system_prompt
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.message_history: List[InputMessage] = []
        self.llm_router = llm_router
        self.stream_callback = stream_callback
        self.conversation_id = conversation_id
        
        # Initialize resource storage
        self.resources: Dict[str, Resource] = {}
        
        # Define context variables that will be available to tools
        self.context_vars = {
            'resources': self.resources,
            'conversation_id': self.conversation_id,
            'stream_callback': self._emit_tool_event  # Add streaming callback to context
        }
        
        # Always use registry tools
        self.tools = tool_registry.to_openai_format()
        
        # Add system message to history
        system_message = Message(
            role="system", 
            content=self.system_prompt
        )
        self.message_history.append(system_message)
        
        # Start conversation tracking if conversation_id is provided
        if self.conversation_id:
            try:
                metadata = {
                    "model": self.model,
                    "reasoning_effort": self.reasoning_effort,
                    "started_at": datetime.now().isoformat()
                }
                chat_storage.start_conversation(self.conversation_id, metadata)
                # Save the initial system message
                chat_storage.append_message(self.conversation_id, system_message)
            except Exception as e:
                logger.warning(f"Failed to start conversation tracking: {e}")

    def step(self, input_message: InputMessage) -> OpenAIResponse:
        """Add an input message and call the LLM API via router"""
        if not self.llm_router:
            raise ValueError("No LLM router configured for this agent")
            
        if input_message is not None:
            self.message_history.append(input_message)
            
            # Save message incrementally
            if self.conversation_id:
                try:
                    chat_storage.append_message(self.conversation_id, input_message)
                except Exception as e:
                    logger.warning(f"Failed to save message incrementally: {e}")
            
            # Log what we're sending to LLM
            if hasattr(input_message, 'content') and input_message.content:
                logger.info(f"→ Sending {input_message.role}: {input_message.content[:200]}{'...' if len(input_message.content) > 200 else ''}")
            else:
                logger.info(f"→ Sending {input_message.role} message")
        else:
            logger.info("→ Continuing conversation after tool execution")
        
        # Clean up any None values that might have accumulated
        self.clean_message_history()
        
        # Prepare tools for API call
        tools = None
        if self.tools:
            tools = [tool.dict() for tool in self.tools]
            
        # Prepare reasoning configuration
        reasoning = None
        if self.reasoning_effort:
            reasoning = {"effort": self.reasoning_effort}
        
        # Call LLM API via router
        try:
            response = self.llm_router.create_completion(
                messages=self.message_history,
                model=self.model,
                tools=tools,
                reasoning=reasoning
            )
            
            # Log what LLM returned with content
            logger.info(f"← LLM response ({len(response.output)} items):")
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
            logger.error(f"LLM API call failed: {e}")
            raise
        
    
    def add_to_history(self, message: InputMessage):
        """Add a message to the conversation history"""
        if message is None:
            logger.error("Attempted to add None message to history")
            return
        self.message_history.append(message)
        
        # Save message incrementally
        if self.conversation_id:
            try:
                chat_storage.append_message(self.conversation_id, message)
            except Exception as e:
                logger.warning(f"Failed to save message incrementally: {e}")
        
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
    
    def _emit_tool_event(self, tool_name: str, status: str, message: str = None, progress: Dict[str, Any] = None, result: str = None, error: str = None):
        """Emit a tool execution event if streaming callback is available"""
        if self.stream_callback:
            event = ToolExecutionResponse(
                tool_name=tool_name,
                status=status,
                message=message,
                progress=progress,
                result=result,
                error=error
            )
            self.stream_callback(event)
    
    def execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a tool call using the tool registry"""
        if not tool_registry.has_tool(tool_call.name):
            error_msg = f"Error: Tool '{tool_call.name}' not found in registry"
            self._emit_tool_event(tool_call.name, "error", error=error_msg)
            return error_msg
        
        try:
            # Emit tool start event
            self._emit_tool_event(tool_call.name, "started", message=f"Starting {tool_call.name}")
            
            # Parse arguments and execute using registry
            args = tool_call.parse_arguments()
            
            # Use agent's context variables for tool execution
            result = tool_registry.execute_tool(tool_call.name, context_vars=self.context_vars, **args)
            
            # Store the raw result for special handling
            self._last_tool_result = {
                'tool_name': tool_call.name,
                'result': result
            }
            
            # Don't emit completion event here - tools handle their own streaming callbacks
            # The tool functions already emit proper completion events with formatted results
            
            # OpenAI API requires string output, but we store the original for special handling
            return str(result)
        except Exception as e:
            error_msg = f"Error executing {tool_call.name}: {str(e)}"
            self._emit_tool_event(tool_call.name, "error", error=error_msg)
            return error_msg
    
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
    