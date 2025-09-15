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
    ChatCompletionTextRequest,
    ChatCompletionVisionRequest,
    ChatCompletionResponse
)


class XLMProvider(BaseLLMProvider):
    """XLM (Z.AI) LLM provider implementation."""
    
    # XLM models that this provider supports (based on the API spec)
    SUPPORTED_MODELS = [
        "glm-4.5v",
        "glm-4.5"  # Vision model
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
    ) -> ChatCompletionResponse:
        """
        Create a chat completion using Z.AI API.
        
        Args:
            messages: List of conversation messages
            model: XLM model name
            tools: Optional list of tools/functions
            reasoning: Optional reasoning configuration (maps to 'thinking')
            **kwargs: Additional Z.AI parameters
            
        Returns:
            ChatCompletionResponse: Standardized response object
        """
        if not self.supports_model(model):
            raise ValueError(f"Model {model} is not supported by XLM provider")
        
        # Create the appropriate request model based on the model type
        if model == "glm-4.5v":
            # Vision model request
            request = ChatCompletionVisionRequest(
                model=model,
                messages=messages,
                tools=tools,
                thinking=reasoning,
                temperature=kwargs.get("temperature", 0.8),
                top_p=kwargs.get("top_p", 0.6),
                max_tokens=kwargs.get("max_tokens", 16384),
                do_sample=kwargs.get("do_sample", True),
                user_id=kwargs.get("user_id"),
                stop=kwargs.get("stop")
            )
        else:
            # Text model request  
            request = ChatCompletionTextRequest(
                model=model,
                messages=messages,
                tools=tools,
                thinking=reasoning,
                temperature=kwargs.get("temperature", 0.6),
                top_p=kwargs.get("top_p", 0.95),
                max_tokens=kwargs.get("max_tokens", 98304),
                do_sample=kwargs.get("do_sample", True),
                user_id=kwargs.get("user_id"),
                stop=kwargs.get("stop"),
                response_format=kwargs.get("response_format")
            )
        
        # Convert to dict for API call
        api_params = request.model_dump(exclude_none=True)
        
        try:
            response = self._make_api_request(api_params)
            chat_response = self._convert_to_chat_completion_response(response)
            return chat_response
            
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
    
    
    
    
    
    
    def _convert_to_chat_completion_response(self, zai_response: Dict[str, Any]) -> ChatCompletionResponse:
        """
        Convert Z.AI response format to ChatCompletionResponse.
        
        Args:
            zai_response: Raw Z.AI API response
            
        Returns:
            ChatCompletionResponse: Standardized response object
        """
        return ChatCompletionResponse.model_validate(zai_response)
