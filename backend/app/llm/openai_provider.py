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
            
            # Add other parameters (filter out unsupported ones and None values)
            supported_params = {
                'temperature', 'max_tokens', 'top_p', 'frequency_penalty', 
                'presence_penalty', 'stop', 'stream', 'user', 'seed',
                'response_format', 'tool_choice', 'reasoning_effort', 'include'
            }
            filtered_kwargs = {
                k: v for k, v in kwargs.items() 
                if k in supported_params and v is not None
            }
            openai_params.update(filtered_kwargs)
            
            # Always include reasoning content if reasoning_effort is specified
            if 'reasoning_effort' in openai_params:
                openai_params['include'] = ['reasoning.encrypted_content']
            
            logger.info(f"Calling OpenAI Chat Completions API with model: {model}")
            logger.info(f"Parameters: {openai_params}")
            raw_response = self.client.chat.completions.create(**openai_params)
            logger.info(f"Raw OpenAI response: {raw_response}")
            logger.info(f"Raw response type: {type(raw_response)}")
            logger.info(f"Raw response dict: {raw_response.model_dump() if hasattr(raw_response, 'model_dump') else 'No model_dump method'}")
            
            # Convert OpenAI response to our ChatCompletionResponse format
            response_dict = {
                "id": raw_response.id,
                "request_id": raw_response.id,  # OpenAI doesn't have separate request_id
                "created": raw_response.created,
                "model": raw_response.model,
                "choices": [],
                "usage": None
            }
            
            # Extract reasoning content from top-level reasoning field if available
            reasoning_content = None
            if hasattr(raw_response, 'reasoning') and raw_response.reasoning:
                logger.info(f"Reasoning field found: {raw_response.reasoning}")
                
                # Try to get encrypted_content first (when include parameter is used)
                if hasattr(raw_response.reasoning, 'encrypted_content') and raw_response.reasoning.encrypted_content:
                    reasoning_content = raw_response.reasoning.encrypted_content
                    logger.info(f"Reasoning encrypted_content extracted: {len(reasoning_content)} characters")
                # Fallback to summary if available
                elif hasattr(raw_response.reasoning, 'summary') and raw_response.reasoning.summary:
                    reasoning_content = raw_response.reasoning.summary
                    logger.info(f"Reasoning summary extracted: {len(reasoning_content)} characters")
                else:
                    logger.info("Reasoning field exists but neither encrypted_content nor summary found")
            else:
                logger.info("No reasoning field found in response")
            
            # Convert choices
            for choice in raw_response.choices:
                choice_dict = {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                        "reasoning_content": reasoning_content,
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
                msg_dict = msg.model_dump()
                
                # Remove tool_calls if it's None or empty list to avoid API errors
                if "tool_calls" in msg_dict and (msg_dict["tool_calls"] is None or msg_dict["tool_calls"] == []):
                    del msg_dict["tool_calls"]
                
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
            tools: List of tool definitions (should already be in OpenAI format from router)
            
        Returns:
            Optional[List[Dict[str, Any]]]: Tools formatted for OpenAI API
        """
        if not tools:
            return None
        
        # Tools should already be in the correct OpenAI format when passed here
        # Just convert to dict if they're Pydantic models
        formatted_tools = []
        for tool in tools:
            if hasattr(tool, 'model_dump'):
                formatted_tools.append(tool.model_dump())
            elif hasattr(tool, 'dict'):
                formatted_tools.append(tool.dict())
            else:
                formatted_tools.append(tool)
        
        return formatted_tools
