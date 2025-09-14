"""
OpenAI provider implementation.

This module implements the OpenAI LLM provider using the existing OpenAI client logic.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger

from .base import BaseLLMProvider
from app.models.chat import InputMessage, ChatCompletionResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    # OpenAI models that this provider supports
    SUPPORTED_MODELS = [
        "gpt-5"
    ]
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            **kwargs: Additional OpenAI client configuration
        """
        super().__init__(api_key, **kwargs)
        self.client = OpenAI(api_key=api_key, **kwargs)
    
    def create_completion(
        self,
        messages: List[InputMessage],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        Create a chat completion using OpenAI API.
        
        Args:
            messages: List of conversation messages
            model: OpenAI model name
            tools: Optional list of tools/functions
            reasoning: Optional reasoning configuration
            **kwargs: Additional OpenAI parameters
            
        Returns:
            ChatCompletionResponse: Standardized response object
        """
        if not self.supports_model(model):
            raise ValueError(f"Model {model} is not supported by OpenAI provider")
        
        # Format messages for OpenAI API
        formatted_messages = self.format_messages_for_api(messages)
        
        
        try:
            # Call OpenAI chat completions API
            logger.info(f"Calling OpenAI API with model: {model}")
            
            # Prepare standard OpenAI API parameters
            openai_params = {
                "model": model,
                "messages": formatted_messages
            }
            
            # Add tools if provided
            if tools:
                formatted_tools = self.format_tools_for_api(tools)
                if formatted_tools:
                    openai_params["tools"] = formatted_tools
            
            # Add other parameters
            openai_params.update(kwargs)
            
            raw_response = self.client.chat.completions.create(**openai_params)
            
            # Convert OpenAI response to our ChatCompletionResponse format
            response_dict = {
                "id": raw_response.id,
                "request_id": raw_response.id,  # OpenAI doesn't have separate request_id
                "created": raw_response.created,
                "model": raw_response.model,
                "choices": [],
                "usage": None
            }
            
            # Convert choices
            for choice in raw_response.choices:
                choice_dict = {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                        "reasoning_content": None,  # OpenAI doesn't have reasoning_content
                        "tool_calls": None
                    },
                    "finish_reason": choice.finish_reason
                }
                
                # Handle tool calls if present
                if choice.message.tool_calls:
                    tool_calls = []
                    for tool_call in choice.message.tool_calls:
                        # Convert OpenAI tool call to our ToolCall format
                        from app.models.chat import ToolCall, ToolCallFunction, ToolType
                        converted_tool_call = ToolCall(
                            id=tool_call.id,
                            type=ToolType.FUNCTION,
                            function=ToolCallFunction(
                                name=tool_call.function.name,
                                arguments=tool_call.function.arguments  # OpenAI returns JSON string
                            )
                        )
                        tool_calls.append(converted_tool_call.model_dump())
                    choice_dict["message"]["tool_calls"] = tool_calls
                
                response_dict["choices"].append(choice_dict)
            
            # Convert usage
            if raw_response.usage:
                response_dict["usage"] = {
                    "prompt_tokens": raw_response.usage.prompt_tokens,
                    "completion_tokens": raw_response.usage.completion_tokens,
                    "total_tokens": raw_response.usage.total_tokens,
                    "prompt_tokens_details": {
                        "cached_tokens": 0  # OpenAI doesn't provide this
                    }
                }
            
            response = ChatCompletionResponse.model_validate(response_dict)
            logger.info(f"← OpenAI response with {len(response.choices)} choices")
            return response
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    
    def format_messages_for_api(self, messages: List[InputMessage]) -> List[Dict[str, Any]]:
        """
        Convert InputMessage objects to OpenAI API format with multimodal support.
        
        Args:
            messages: List of InputMessage objects
            
        Returns:
            List[Dict[str, Any]]: Messages formatted for OpenAI API
        """
        formatted_messages = []
        for msg in messages:
            if msg is not None:
                msg_dict = msg.dict()
                
                # Handle multimodal content (ensure image_url format is preserved)
                content = msg_dict["content"]
                if isinstance(content, list):
                    # Multimodal content - ensure proper format for OpenAI
                    formatted_content = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                formatted_content.append({
                                    "type": "text",
                                    "text": item.get("text", "")
                                })
                            elif item.get("type") == "image_url":
                                formatted_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": item.get("image_url", {}).get("url", "")
                                    }
                                })
                    msg_dict["content"] = formatted_content
                
                formatted_messages.append(msg_dict)
        return formatted_messages
    
    def format_tools_for_api(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        Format tools for OpenAI API.
        
        Args:
            tools: List of tool definitions
            
        Returns:
            Optional[List[Dict[str, Any]]]: Tools formatted for OpenAI API
        """
        if not tools:
            return None
        
        # OpenAI expects tools to be in a specific format
        # The existing tool registry should already provide the correct format
        return tools
