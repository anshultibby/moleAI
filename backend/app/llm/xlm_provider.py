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
    ZAITool,
    ZAIToolCall,
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
                    # Let Pydantic discriminated union handle the routing automatically
                    zai_tools.append(ZAITool.model_validate(tool))
                except Exception as e:
                    logger.error(f"Error converting tool: {e}")
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
        
        # Convert to dict for API call
        api_params = zai_request.dict(exclude_none=True)
        
        try:
            # Call Z.AI API
            logger.info(f"Calling Z.AI API with model: {model}")
            response = self._make_api_request(api_params)
            
            # Convert Z.AI response to OpenAI format
            openai_response = self._convert_xlm_to_openai_response(response, model)
            
            logger.info(f"← Z.AI response converted to OpenAI format")
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
        zai_messages = []
        
        for msg in messages:
            if msg is None:
                continue
            
            # Only process Message objects (skip ToolCall, ToolCallOutput, etc.)
            if not isinstance(msg, Message):
                logger.debug(f"Skipping non-Message type: {type(msg).__name__}")
                continue
                
            
            try:
                # Use Pydantic models directly for all conversion
                role = getattr(msg, 'role', None)
                content = getattr(msg, 'content', "")
                
                msg_data = {
                    "role": role,
                    "content": ContentConverter.prepare_content(content, role),
                }
                
                # Add optional fields using Pydantic validation
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls = []
                    for call in msg.tool_calls:
                        # Let Pydantic discriminated union handle tool call routing
                        tool_calls.append(ZAIToolCall.model_validate(call).model_dump())
                    msg_data["tool_calls"] = tool_calls
                    
                if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
                    msg_data["tool_call_id"] = msg.tool_call_id
                elif hasattr(msg, 'call_id') and msg.call_id:
                    msg_data["tool_call_id"] = msg.call_id
                
                # Pydantic discriminated union handles message type routing automatically
                zai_message = ZAIMessage.model_validate(msg_data)
                zai_messages.append(zai_message)
                        
            except Exception as e:
                logger.error(f"Error converting message: {e}")
                continue
        
        return zai_messages
    
    
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
            status="completed"
        )
