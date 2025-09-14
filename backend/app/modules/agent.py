from typing import List, Optional, Generator, Dict, Any, Callable
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
from app.models.chat import ToolCall, ToolExecutionResponse
from app.models.resource import Resource
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
        
        # Initialize resource storage
        self.resources: Dict[str, Resource] = {}
        
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
    
    
    def run(self, initial_message: Message) -> ChatCompletionResponse:
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
        try:
            messages_with_checklist = self._prepare_messages_with_checklist()
            
            response = self.llm_router.create_completion(
                messages=messages_with_checklist,
                model=self.model,
                tools=self.tools,
                thinking=self.thinking
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
                    # Execute the tool (tool_call should already be in the right format)
                    tool_result = self.execute_tool_call(tool_call)
                    
                    # Add tool result to history
                    tool_msg = ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call.id
                    )
                    self.add_to_history(tool_msg)
                
                messages_with_checklist = self._prepare_messages_with_checklist()
                
                try:
                    response = self.llm_router.create_completion(
                        messages=messages_with_checklist,
                        model=self.model,
                        tools=self.tools,
                        thinking=self.thinking
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
        
        return response
    
    def get_message_history(self) -> List[Message]:
        return self.message_history.copy()
    
    def get_system_prompt(self) -> str:
        return self.system_prompt
    
    