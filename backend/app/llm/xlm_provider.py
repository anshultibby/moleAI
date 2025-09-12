"""
XLM (Z.AI) provider implementation.

This module implements the XLM LLM provider using the Z.AI API specification.
"""

import requests
from typing import List, Dict, Any, Optional, Union
from loguru import logger

from .base import BaseLLMProvider
from app.models.chat import (
    InputMessage, 
    OpenAIResponse,
    Message
)
from .xlm_models import (
    ZAIRequest,
    ZAIThinking,
    ZAIMessage,
    ZAISystemMessage,
    ZAIUserMessage,
    ZAIAssistantMessage,
    ZAIToolMessage,
    ZAITool,
    ZAIFunctionTool,
    ZAIToolCall,
    ZAIFunctionToolCall,
    ZAIResponse,
    ContentConverter
)


class XLMProvider(BaseLLMProvider):
    """XLM (Z.AI) LLM provider implementation."""
    
    # XLM models that this provider supports (based on the API spec)
    SUPPORTED_MODELS = [
        "glm-4.5v"  # Vision model
    ]
    
    # API endpoint
    API_BASE_URL = "https://api.z.ai/api"
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize XLM provider.
        
        Args:
            api_key: Z.AI API key
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get('base_url', self.API_BASE_URL)
    
    def create_completion(
        self,
        messages: List[InputMessage],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> OpenAIResponse:
        """
        Create a chat completion using Z.AI API.
        
        Args:
            messages: List of conversation messages
            model: XLM model name
            tools: Optional list of tools/functions
            reasoning: Optional reasoning configuration (maps to 'thinking')
            **kwargs: Additional Z.AI parameters
            
        Returns:
            OpenAIResponse: Standardized response object
        """
        if not self.supports_model(model):
            raise ValueError(f"Model {model} is not supported by XLM provider")
        
        # Convert messages to Z.AI format using Pydantic models
        zai_messages = self._convert_to_zai_messages(messages)
        
        # Convert tools to Z.AI format using Pydantic
        zai_tools = None
        if tools:
            zai_tools = []
            for tool in tools:
                try:
                    # Convert our Tool model to Z.AI format
                    if hasattr(tool, 'type') and tool.type == "function":
                        # Convert to Z.AI function tool format
                        zai_tool = ZAIFunctionTool(
                            type="function",
                            function={
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.parameters
                            }
                        )
                        zai_tools.append(zai_tool)
                    elif isinstance(tool, dict):
                        # Handle dict format
                        if tool.get("type") == "function":
                            zai_tool = ZAIFunctionTool(
                                type="function",
                                function={
                                    "name": tool.get("name", ""),
                                    "description": tool.get("description", ""),
                                    "parameters": tool.get("parameters", {})
                                }
                            )
                            zai_tools.append(zai_tool)
                        else:
                            # Try direct validation for other tool types
                            zai_tools.append(ZAITool.model_validate(tool))
                    else:
                        # Try direct validation
                        zai_tools.append(ZAITool.model_validate(tool))
                except Exception as e:
                    logger.error(f"Error converting tool {getattr(tool, 'name', 'unknown')}: {e}")
                    continue
        
        # Convert reasoning to thinking
        zai_thinking = None
        if reasoning:
            zai_thinking = ZAIThinking(
                type="enabled" if reasoning.get("effort") != "disabled" else "disabled"
            )
        
        # Create Z.AI request using Pydantic model
        zai_request = ZAIRequest(
            model=model,
            messages=zai_messages,
            tools=zai_tools,
            thinking=zai_thinking,
            temperature=kwargs.get("temperature", 0.6),
            top_p=kwargs.get("top_p", 0.95),
            max_tokens=kwargs.get("max_tokens", 1024),
            do_sample=kwargs.get("do_sample", True),
            user_id=kwargs.get("user_id"),
            stop=kwargs.get("stop"),
            response_format=kwargs.get("response_format")
        )
        
        api_params = zai_request.dict(exclude_none=True)
        
        try:
            response = self._make_api_request(api_params)
            openai_response = self._convert_xlm_to_openai_response(response, model)
            return openai_response
            
        except Exception as e:
            logger.error(f"Z.AI API call failed: {e}")
            raise
    
    
    def _make_api_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to Z.AI API.
        
        Args:
            params: API request parameters
            
        Returns:
            Dict[str, Any]: API response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en"
        }
        
        url = f"{self.base_url}/paas/v4/chat/completions"
        
        response = requests.post(
            url,
            headers=headers,
            json=params,
            timeout=60
        )
        
        if response.status_code != 200:
            error_msg = f"Z.AI API returned status {response.status_code}: {response.text}"
            raise Exception(error_msg)
        
        return response.json()
    
    def _convert_to_zai_messages(self, messages: List[InputMessage]) -> List[ZAIMessage]:
        """
        Convert InputMessage objects to Z.AI message format using Pydantic models.
        
        Args:
            messages: List of InputMessage objects
            
        Returns:
            List[ZAIMessage]: Messages in Z.AI format
        """
        from app.models.chat import InputReasoningItem, InputFunctionToolCall, ToolCallOutput
        
        zai_messages = []
        
        for msg in messages:
            if msg is None:
                continue
            
            # Handle different message types
            if isinstance(msg, Message):
                # Handle standard Message objects
                zai_message = self._convert_message_to_zai(msg)
                if zai_message:
                    zai_messages.append(zai_message)
            elif isinstance(msg, InputReasoningItem):
                # Convert reasoning item to assistant message with reasoning content
                zai_message = self._convert_reasoning_to_zai(msg)
                if zai_message:
                    zai_messages.append(zai_message)
            elif isinstance(msg, InputFunctionToolCall):
                # Convert function tool call to assistant message with tool calls
                zai_message = self._convert_function_tool_call_to_zai(msg)
                if zai_message:
                    zai_messages.append(zai_message)
            elif isinstance(msg, ToolCallOutput):
                # Convert tool call output to tool message
                zai_message = self._convert_tool_output_to_zai(msg)
                if zai_message:
                    zai_messages.append(zai_message)
            else:
                logger.debug(f"Skipping unsupported message type: {type(msg).__name__}")
                continue
        
        return zai_messages
    
    def _convert_message_to_zai(self, msg: Message) -> Optional[ZAIMessage]:
        """Convert a standard Message object to ZAI format."""
        try:
            role = getattr(msg, 'role', None)
            content = getattr(msg, 'content', "")
            
            # Ensure content is never empty - Z.AI API requires non-empty content
            if not content:
                logger.warning(f"Empty content for {role} message, skipping")
                return None
            
            # Convert content based on role and type
            if role == "system":
                # System messages must have string content
                content_str = self._extract_text_content(content)
                if not content_str:
                    logger.warning(f"Empty system message content, skipping")
                    return None
                return ZAISystemMessage(role="system", content=content_str)
                
            elif role == "user":
                # User messages can be string or multimodal
                if isinstance(content, str):
                    return ZAIUserMessage(role="user", content=content)
                else:
                    # Try to extract text content for now (multimodal support can be added later)
                    content_str = self._extract_text_content(content)
                    if not content_str:
                        logger.warning(f"Empty user message content, skipping")
                        return None
                    return ZAIUserMessage(role="user", content=content_str)
                    
            elif role == "assistant":
                # Assistant messages may have tool calls
                content_str = self._extract_text_content(content) if content else ""
                
                tool_calls = None
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls = []
                    for call in msg.tool_calls:
                        try:
                            # Convert tool call to Z.AI format
                            zai_tool_call = ZAIFunctionToolCall(
                                id=getattr(call, 'id', getattr(call, 'call_id', '')),
                                type="function",
                                function={
                                    "name": getattr(call, 'name', ''),
                                    "arguments": getattr(call, 'arguments', '{}')
                                }
                            )
                            tool_calls.append(zai_tool_call)
                        except Exception as e:
                            logger.error(f"Error converting tool call: {e}")
                            continue
                
                return ZAIAssistantMessage(
                    role="assistant", 
                    content=content_str,
                    tool_calls=tool_calls
                )
                
            elif role == "tool":
                # Tool messages need tool_call_id
                content_str = self._extract_text_content(content)
                if not content_str:
                    logger.warning(f"Empty tool message content, skipping")
                    return None
                    
                tool_call_id = getattr(msg, 'tool_call_id', getattr(msg, 'call_id', ''))
                if not tool_call_id:
                    logger.warning(f"Tool message missing tool_call_id, skipping")
                    return None
                    
                return ZAIToolMessage(
                    role="tool",
                    content=content_str,
                    tool_call_id=tool_call_id
                )
                
            else:
                logger.warning(f"Unknown message role: {role}, skipping")
                return None
                    
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            return None
    
    def _convert_reasoning_to_zai(self, reasoning: 'InputReasoningItem') -> Optional[ZAIMessage]:
        """Convert InputReasoningItem to ZAI assistant message with reasoning content."""
        try:
            # Extract reasoning content
            content = reasoning.content or ""
            if reasoning.summary:
                # Combine summary with content
                summary_text = " ".join(reasoning.summary)
                if content:
                    content = f"{summary_text}\n\n{content}"
                else:
                    content = summary_text
            
            if not content:
                logger.warning("Empty reasoning content, skipping")
                return None
            
            # Create assistant message with reasoning content
            # Note: Z.AI doesn't have a specific reasoning message type in the request,
            # but we can include reasoning content in an assistant message
            return ZAIAssistantMessage(
                role="assistant",
                content=content
            )
            
        except Exception as e:
            logger.error(f"Error converting reasoning item: {e}")
            return None
    
    def _convert_function_tool_call_to_zai(self, tool_call: 'InputFunctionToolCall') -> Optional[ZAIMessage]:
        """Convert InputFunctionToolCall to ZAI assistant message with tool calls."""
        try:
            # Create ZAI tool call
            zai_tool_call = ZAIFunctionToolCall(
                id=tool_call.id or tool_call.call_id,
                type="function",
                function={
                    "name": tool_call.name,
                    "arguments": tool_call.arguments
                }
            )
            
            # Create assistant message with tool calls
            return ZAIAssistantMessage(
                role="assistant",
                content="",  # Empty content when tool calls are present
                tool_calls=[zai_tool_call]
            )
            
        except Exception as e:
            logger.error(f"Error converting function tool call: {e}")
            return None
    
    def _convert_tool_output_to_zai(self, tool_output: 'ToolCallOutput') -> Optional[ZAIMessage]:
        """Convert ToolCallOutput to ZAI tool message."""
        try:
            if not tool_output.output:
                logger.warning("Empty tool output content, skipping")
                return None
            
            return ZAIToolMessage(
                role="tool",
                content=tool_output.output,
                tool_call_id=tool_output.call_id
            )
            
        except Exception as e:
            logger.error(f"Error converting tool output: {e}")
            return None
    
    def _extract_text_content(self, content: Any) -> str:
        """Extract text content from various content formats."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, dict) and item.get("type") == "input_text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return " ".join(text_parts) if text_parts else ""
        else:
            return str(content) if content else ""
    
    
    def _convert_xlm_to_openai_response(self, xlm_response: Dict[str, Any], model: str) -> OpenAIResponse:
        """
        Convert Z.AI response format to OpenAI response format using Pydantic models.
        
        Args:
            xlm_response: Raw Z.AI API response
            model: Model name used
            
        Returns:
            OpenAIResponse: Standardized response object
        """
        from app.models.chat import (
            ResponseReasoningItem, ResponseFunctionToolCall,
            ResponseOutputMessage, ResponseOutputText, ResponseUsage,
            InputTokensDetails, OutputTokensDetails
        )
        
        # Parse Z.AI response using Pydantic
        zai_response = ZAIResponse.model_validate(xlm_response)
        
        # Extract the first choice
        choice = zai_response.choices[0] if zai_response.choices else None
        if not choice:
            raise ValueError("No choices in Z.AI response")
        
        message = choice.message
        output_items = []
        
        # Handle reasoning content if present
        if message.reasoning_content:
            reasoning_item = ResponseReasoningItem(
                id=f"{zai_response.id}-reasoning",
                content=message.reasoning_content,
                status="completed"
            )
            output_items.append(reasoning_item)
        
        # Handle tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_item = ResponseFunctionToolCall(
                    id=tool_call.id,
                    call_id=tool_call.id,
                    name=tool_call.function["name"],
                    arguments=tool_call.function["arguments"],
                    status="completed"
                )
                output_items.append(tool_item)
        
        # Handle regular message content
        if message.content:
            text_content = ResponseOutputText(text=message.content)
            message_item = ResponseOutputMessage(
                id=f"{zai_response.id}-msg",
                content=[text_content],
                role="assistant"
            )
            output_items.append(message_item)
        
        # Create usage object
        usage = ResponseUsage(
            input_tokens=zai_response.usage.prompt_tokens,
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens=zai_response.usage.completion_tokens,
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
            total_tokens=zai_response.usage.total_tokens
        )
        
        # Create OpenAI-compatible response
        return OpenAIResponse(
            id=zai_response.id,
            created_at=float(zai_response.created),
            model=model,
            output=output_items,
            usage=usage,
            status="completed",
            finish_reason=choice.finish_reason
        )
