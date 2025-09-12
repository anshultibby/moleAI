"""
OpenAI provider implementation.

This module implements the OpenAI LLM provider using the existing OpenAI client logic.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger

from .base import BaseLLMProvider
from app.models.chat import InputMessage, OpenAIResponse


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
    ) -> OpenAIResponse:
        """
        Create a chat completion using OpenAI API.
        
        Args:
            messages: List of conversation messages
            model: OpenAI model name
            tools: Optional list of tools/functions
            reasoning: Optional reasoning configuration
            **kwargs: Additional OpenAI parameters
            
        Returns:
            OpenAIResponse: Standardized response object
        """
        if not self.supports_model(model):
            raise ValueError(f"Model {model} is not supported by OpenAI provider")
        
        # Format messages for OpenAI API
        formatted_messages = self.format_messages_for_api(messages)
        
        # Prepare API call parameters
        api_params = {
            "model": model,
            "input": formatted_messages
        }
        
        # Add tools if provided
        if tools:
            formatted_tools = self.format_tools_for_api(tools)
            if formatted_tools:
                api_params["tools"] = formatted_tools
        
        # Add reasoning if provided
        if reasoning:
            api_params["reasoning"] = reasoning
        
        # Add any additional parameters
        api_params.update(kwargs)
        
        try:
            # Call OpenAI responses API
            logger.info(f"Calling OpenAI API with model: {model}")
            raw_response = self.client.responses.create(**api_params)
            
            # Parse response using Pydantic model for type safety
            raw_dict = raw_response.dict()
            
            # Handle reasoning field - if it exists but has None effort, set a default
            if "reasoning" in raw_dict and raw_dict["reasoning"] is not None:
                if "effort" not in raw_dict["reasoning"] or raw_dict["reasoning"]["effort"] is None:
                    raw_dict["reasoning"]["effort"] = "medium"
            
            response = OpenAIResponse.parse_obj(raw_dict)
            
            logger.info(f"← OpenAI response ({len(response.output)} items)")
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
