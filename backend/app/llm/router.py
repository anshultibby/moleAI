"""
LLM Router for routing requests to appropriate providers.

This module provides a router that automatically selects the correct LLM provider
based on the model name and routes requests accordingly.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from .base import BaseLLMProvider
from .xlm_provider import XLMProvider
from app.models import (
    Message, 
    ChatCompletionResponse, 
    ModelType,
    ChatCompletionRequest,
    ChatCompletionTextRequest,
    ChatCompletionVisionRequest
)


class LLMRouter:
    """Router for GLM-4.5V model via XLM provider."""
    
    def __init__(self, xlm_api_key: str):
        """
        Initialize the LLM router with XLM API key for GLM-4.5V.
        
        Args:
            xlm_api_key: XLM (Z.AI) API key for GLM models
        """
        if not xlm_api_key:
            raise ValueError("XLM API key is required for GLM-4.5V model")
            
        self.xlm_provider = XLMProvider(xlm_api_key)
        self.default_model = ModelType.GLM_4_5
        
        logger.info(f"LLM Router initialized with GLM-4.5V as default model")
    
    def get_provider_for_model(self, model: str) -> BaseLLMProvider:
        """
        Get the XLM provider (only provider we support).
        
        Args:
            model: Model name (should be GLM model)
            
        Returns:
            BaseLLMProvider: The XLM provider
            
        Raises:
            ValueError: If model is not supported
        """
        if not self.xlm_provider.supports_model(model):
            supported_models = self.xlm_provider.get_supported_models()
            raise ValueError(
                f"Model '{model}' not supported. "
                f"Supported models: {', '.join(supported_models)}"
            )
        
        return self.xlm_provider
    
    def create_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        Create a chat completion.
        
        Args:
            messages: List of conversation messages
            model: Model name (defaults to GLM-4.5V)
            tools: Optional list of tools/functions
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            ChatCompletionResponse: Response object
        """
        target_model = model or self.default_model
        
        # Create appropriate request based on model type
        if target_model == ModelType.GLM_4_5:
            request = ChatCompletionTextRequest(
                model=target_model,
                messages=messages,
                tools=tools,
                **kwargs
            )
        else:  # GLM_4_5V or other vision models
            request = ChatCompletionVisionRequest(
                model=target_model,
                messages=messages,
                tools=tools,
                **kwargs
            )
        
        provider = self.get_provider_for_model(target_model)
        return provider.create_completion(
            messages=request.messages,
            model=target_model,
            tools=getattr(request, 'tools', None),
            reasoning=getattr(request, 'thinking', None),
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            stream=request.stream,
            do_sample=request.do_sample,
            user_id=getattr(request, 'user_id', None),
            stop=getattr(request, 'stop', None),
            response_format=getattr(request, 'response_format', None),
            request_id=getattr(request, 'request_id', None)
        )
    
    def supports_model(self, model: str) -> bool:
        """
        Check if the XLM provider supports the given model.
        
        Args:
            model: Model name to check
            
        Returns:
            bool: True if the model is supported
        """
        return self.xlm_provider.supports_model(model)
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models.
        
        Returns:
            List[str]: List of supported model names
        """
        return self.xlm_provider.get_supported_models()
    
    def get_default_model(self) -> str:
        """
        Get the default model (GLM-4.5V).
        
        Returns:
            str: Default model name
        """
        return self.default_model
