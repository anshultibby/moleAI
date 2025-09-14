from typing import List, Optional, Generator, Dict, Any, Callable, AsyncGenerator
import json
from datetime import datetime
from loguru import logger
from app.models import (
    Message, 
    SystemMessage,
    AssistantMessage,
    ToolMessage,
    ChatCompletionResponse,
    ChatThinking,
    ThinkingType,
)
from app.models.chat import (
    ToolCall, 
    ToolExecutionResponse,
    StreamEventType,
    LLMCallStatus,
    ToolExecutionStatus,
    LLMCallEvent,
    ThinkingEvent,
    ToolExecutionEvent,
    MessageEvent,
    ProductGridEvent,
    ProductEvent,
    CompleteEvent,
    ErrorEvent,
    StreamingEvent
)
from app.models.resource import Resource
from app.models.product_collection import ProductCollection
from app.tools import tool_registry
from app.utils.chat_storage import chat_storage
from app.llm.router import LLMRouter

# Configuration constants
MAX_TOOL_CALLS_PER_TURN = 45


class ToolCallLimitHelper:
    """Helper to manage tool call limits and provide clean limit checking"""
    
    def __init__(self, max_calls: int = MAX_TOOL_CALLS_PER_TURN):
        self.max_calls = max_calls
        self.current_count = 0
    
    def reset(self):
        """Reset the counter for a new conversation turn"""
        self.current_count = 0
    
    def increment(self):
        """Increment the tool call counter"""
        self.current_count += 1
    
    def is_limit_reached(self) -> bool:
        """Check if the limit has been reached"""
        return self.current_count >= self.max_calls
    
    def get_limit_message(self) -> str:
        """Get the standard limit reached message"""
        return f"Reached maximum of {self.max_calls} tool calls. Please provide further instructions or ask me to continue."
    
    def create_limit_event(self, stream_callback) -> None:
        """Create and emit a tool limit event"""
        if stream_callback:
            event = ToolExecutionResponse(
                tool_name="system",
                status="turn_limit_exceeded",
                message=self.get_limit_message(),
                progress={"current_turns": self.current_count, "max_turns": self.max_calls}
            )
            stream_callback(event)
    
    def handle_limit_exceeded(self, agent, response):
        """Handle the complete limit exceeded flow"""
        # Emit turn limit event
        self.create_limit_event(agent.stream_callback)
        
        # Return the limit message
        return self.get_limit_message()


class Agent:
    def __init__(self, 
                 system_prompt: str, 
                 model: str, 
                 reasoning_effort: str = "medium",
                 llm_router: Optional[LLMRouter] = None,
                 stream_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                 conversation_id: Optional[str] = None):
        self.system_prompt = system_prompt
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.message_history: List[Message] = []
        self.llm_router = llm_router
        self.stream_callback = stream_callback
        self.conversation_id = conversation_id
        
        # Prepare thinking configuration once
        self.thinking = None
        if self.reasoning_effort:
            self.thinking = ChatThinking(type=ThinkingType.ENABLED)
        
        # Initialize resource storage - now stores ProductCollection objects directly
        self.resources: Dict[str, ProductCollection] = {}
        
        # Initialize checklist storage
        self.checklist: Optional[Dict[str, Any]] = None

        
        # Define context variables that will be available to tools
        self.context_vars = {
            'resources': self.resources,
            'conversation_id': self.conversation_id,
            'stream_callback': self._emit_tool_event,  # Add streaming callback to context
            'agent': self  # Add reference to agent for checklist access
        }
        
        # Always use registry tools
        self.tools = tool_registry.to_openai_format()
        
        # Add system message to history
        system_message = SystemMessage(content=self.system_prompt)
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


    def add_to_history(self, message: Message):
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
    
    def _prune_message_history(self) -> List[Message]:
        """
        Prune message history to keep only essential messages:
        1. System message (initial system prompt)
        2. Initial user message (first user message)
        3. Checklist-related system messages
        4. Recent context (last few exchanges for immediate context)
        """
        if not self.message_history:
            return []
        
        pruned_messages = []
        
        # Always keep the first system message (system prompt)
        system_message = None
        initial_user_message = None
        checklist_messages = []
        recent_messages = []
        
        # Find essential messages
        for i, message in enumerate(self.message_history):
            if hasattr(message, 'role'):
                if message.role == "system":
                    if system_message is None:
                        # First system message is the system prompt
                        system_message = message
                    elif hasattr(message, 'content') and message.content and "CHECKLIST" in message.content:
                        # This is a checklist message
                        checklist_messages.append(message)
                elif message.role == "user" and initial_user_message is None:
                    # First user message
                    initial_user_message = message
        
        # Get recent messages (last 6 messages for immediate context)
        # Skip if they're already captured above
        recent_count = 30
        for message in self.message_history[-recent_count:]:
            if (message != system_message and 
                message != initial_user_message and 
                message not in checklist_messages):
                recent_messages.append(message)
        
        # Build pruned history in order
        if system_message:
            pruned_messages.append(system_message)
        
        if initial_user_message:
            pruned_messages.append(initial_user_message)
        
        # Add checklist messages (they contain current state)
        pruned_messages.extend(checklist_messages)
        
        # Add recent context
        pruned_messages.extend(recent_messages)
        
        logger.info(f"Pruned history: {len(self.message_history)} -> {len(pruned_messages)} messages")
        return pruned_messages

    def _prepare_messages_with_checklist(self) -> List[Message]:
        """Prepare messages including checklist as the last message if it exists"""
        # Use pruned history instead of full history
        messages = self._prune_message_history()
        
        # If checklist exists, add it as the last message
        if self.checklist:
            checklist_content = f"CURRENT CHECKLIST:\n{json.dumps(self.checklist, indent=2)}\n\nAlways check if any checklist items can be marked as completed based on the conversation and use it to guide your actions."
            
            checklist_message = SystemMessage(content=checklist_content)
            messages.append(checklist_message)
        
        return messages
    
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
    
    async def _handle_display_items_result(self, tool_result: str, tool_call_id: str):
        """Handle display_items tool result and stream products"""
        try:
            # Parse the tool result as JSON
            if isinstance(tool_result, str):
                try:
                    result_data = json.loads(tool_result)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse display_items result as JSON: {tool_result}")
                    return
            else:
                # tool_result is already a dict (shouldn't happen with current implementation)
                result_data = tool_result
            
            # Check if this is an error result
            if isinstance(result_data, dict) and result_data.get('error'):
                logger.warning(f"display_items tool returned error: {result_data['error']}")
                return
            
            # Check if this is a successful display_items result
            if (isinstance(result_data, dict) and 
                result_data.get('stream_products') and 
                result_data.get('items')):
                
                # Stream product grid event
                yield ProductGridEvent(
                    title=result_data.get('title', 'Products Found'),
                    products=result_data['items'],
                    count=len(result_data['items']),
                    timestamp=datetime.now().isoformat()
                )
                
                # Optionally stream individual products for real-time effect
                for product in result_data['items']:
                    yield ProductEvent(
                        product=product,
                        timestamp=datetime.now().isoformat()
                    )
                    # Small delay for streaming effect (optional)
                    import asyncio
                    await asyncio.sleep(0.1)
                    
        except (TypeError, KeyError) as e:
            logger.warning(f"Failed to process display_items result: {e}")
            # Don't yield anything if processing fails
    
    def execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a tool call using the tool registry"""
        tool_name = tool_call.function.name if tool_call.function else "unknown"
        
        if not tool_registry.has_tool(tool_name):
            error_msg = f"Error: Tool '{tool_name}' not found in registry"
            self._emit_tool_event(tool_name, "error", error=error_msg)
            return error_msg
        
        try:
            # Emit tool start event
            self._emit_tool_event(tool_name, "started", message=f"Starting {tool_name}")
            
            # Parse arguments and execute using registry
            args = tool_call.parse_arguments()
            
            # Use agent's context variables for tool execution
            result = tool_registry.execute_tool(tool_name, context_vars=self.context_vars, **args)
            
            
            # Don't emit completion event here - tools handle their own streaming callbacks
            # The tool functions already emit proper completion events with formatted results
            
            # OpenAI API requires string output, but convert dicts to JSON for proper parsing
            if isinstance(result, dict):
                return json.dumps(result)
            else:
                return str(result)
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            self._emit_tool_event(tool_name, "error", error=error_msg)
            return error_msg
    
    
    async def run(self, initial_message: Message) -> AsyncGenerator[StreamingEvent, None]:
        """
        Process a message and handle tool calls, continuing the conversation until completion.
        Returns the final response from the LLM.
        """
        if not self.llm_router:
            raise ValueError("No LLM router configured for this agent")
        
        # Add initial message to history
        self.message_history.append(initial_message)
        
        # Save message incrementally
        if self.conversation_id:
            try:
                chat_storage.append_message(self.conversation_id, initial_message)
            except Exception as e:
                logger.warning(f"Failed to save message incrementally: {e}")
        
        # Make initial LLM call
        yield LLMCallEvent(
            status=LLMCallStatus.STARTED,
            message="Making initial LLM call",
            timestamp=datetime.now().isoformat()
        )
        
        try:
            messages_with_checklist = self._prepare_messages_with_checklist()
            
            response = self.llm_router.create_completion(
                messages=messages_with_checklist,
                model=self.model,
                tools=self.tools,
                thinking=self.thinking
            )
            
            # Yield thinking content if available
            if response.choices and response.choices[0].message.reasoning_content:
                yield ThinkingEvent(
                    content=response.choices[0].message.reasoning_content,
                    timestamp=datetime.now().isoformat()
                )
            
            # Log what LLM returned
            if response.choices:
                choice = response.choices[0]
                if choice.message.content:
                    logger.info(f"← LLM response: {choice.message.content[:200]}{'...' if len(choice.message.content) > 200 else ''}")
                if choice.message.tool_calls:
                    logger.info(f"← LLM tool calls: {len(choice.message.tool_calls)} calls")
                if choice.message.reasoning_content:
                    logger.info(f"← LLM reasoning: {choice.message.reasoning_content[:200]}{'...' if len(choice.message.reasoning_content) > 200 else ''}")
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            yield ErrorEvent(
                error=f"LLM API call failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
            raise
        
        # Continue processing until we get a final response or hit limits
        while response.choices:
            choice = response.choices[0]
            
            # Check if conversation should stop based on finish reason
            if choice.finish_reason in ["stop", "length"]:
                # Add final assistant response to history and stop
                if choice.message.content:
                    assistant_msg = AssistantMessage(content=choice.message.content)
                    self.add_to_history(assistant_msg)
                break
            
            # Check if we have tool calls to execute
            if choice.message.tool_calls:
                
                assistant_msg = AssistantMessage(
                    content=choice.message.content,
                    tool_calls=choice.message.tool_calls
                )
                self.add_to_history(assistant_msg)
                
                # Execute each tool call and add results to history
                for tool_call in choice.message.tool_calls:
                    # Yield tool execution start event
                    yield ToolExecutionEvent(
                        tool_name=tool_call.function.name,
                        status=ToolExecutionStatus.STARTED,
                        tool_call_id=tool_call.id,
                        timestamp=datetime.now().isoformat()
                    )
                    
                    # Execute the tool (tool_call should already be in the right format)
                    tool_result = self.execute_tool_call(tool_call)
                    
                    # Check if this is display_items tool and handle product streaming
                    if tool_call.function.name == "display_items":
                        async for product_event in self._handle_display_items_result(tool_result, tool_call.id):
                            yield product_event
                    
                    # Yield tool execution completion event
                    yield ToolExecutionEvent(
                        tool_name=tool_call.function.name,
                        status=ToolExecutionStatus.COMPLETED,
                        tool_call_id=tool_call.id,
                        result=str(tool_result),
                        timestamp=datetime.now().isoformat()
                    )
                    
                    # Add tool result to history
                    tool_msg = ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call.id
                    )
                    self.add_to_history(tool_msg)
                
                # Yield continuation LLM call event
                yield LLMCallEvent(
                    status=LLMCallStatus.CONTINUING,
                    message="Continuing conversation after tool execution",
                    timestamp=datetime.now().isoformat()
                )
                
                messages_with_checklist = self._prepare_messages_with_checklist()
                
                try:
                    response = self.llm_router.create_completion(
                        messages=messages_with_checklist,
                        model=self.model,
                        tools=self.tools,
                        thinking=self.thinking
                    )
                    
                    # Yield thinking content if available
                    if response.choices and response.choices[0].message.reasoning_content:
                        yield ThinkingEvent(
                            content=response.choices[0].message.reasoning_content,
                            timestamp=datetime.now().isoformat()
                        )
                except Exception as e:
                    logger.error(f"LLM API call failed during tool execution: {e}")
                    error_msg = f"Error during conversation continuation: {str(e)}"
                    assistant_msg = AssistantMessage(content=error_msg)
                    self.add_to_history(assistant_msg)
                    choice.message.content = error_msg
                    choice.message.tool_calls = None
                    break
                    
            else:
                if choice.message.content:
                    assistant_msg = AssistantMessage(content=choice.message.content)
                    self.add_to_history(assistant_msg)
        
        # Yield final response
        if response.choices and response.choices[0].message.content:
            yield MessageEvent(
                content=response.choices[0].message.content,
                final=True,
                timestamp=datetime.now().isoformat()
            )
        
        # Yield completion event
        yield CompleteEvent(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    
    def get_message_history(self) -> List[Message]:
        return self.message_history.copy()
    
    def get_system_prompt(self) -> str:
        return self.system_prompt
    
    