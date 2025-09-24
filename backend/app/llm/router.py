"""
LLM Router for routing requests to appropriate providers.

This module provides a router that automatically selects the correct LLM provider
based on the model name and routes requests accordingly.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from .base import BaseLLMProvider
from .xlm_provider import XLMProvider
from .openai_provider import OpenAIProvider
from app.models import (
    Message, 
    ChatCompletionResponse, 
    ModelType,
    ChatCompletionRequest,
    ChatCompletionTextRequest,
    ChatCompletionVisionRequest
)


class LLMRouter:
    """Router for routing requests to appropriate LLM providers."""
    
    def __init__(self, openai_api_key: str, xlm_api_key: str = None):
        """
        Initialize the LLM router with API keys.
        
        Args:
            openai_api_key: OpenAI API key for GPT models
            xlm_api_key: XLM (Z.AI) API key for GLM models (optional)
        """
        if not openai_api_key:
            raise ValueError("OpenAI API key is required for GPT models")
            
        self.openai_provider = OpenAIProvider(openai_api_key)
        self.xlm_provider = XLMProvider(xlm_api_key) if xlm_api_key else None
        self.default_model = ModelType.GPT_5
        
        logger.info(f"LLM Router initialized with GPT-5 as default model")
    
    def get_provider_for_model(self, model: str) -> BaseLLMProvider:
        """
        Get the appropriate provider for the given model.
        
        Args:
            model: Model name
            
        Returns:
            BaseLLMProvider: The appropriate provider
            
        Raises:
            ValueError: If model is not supported
        """
        # Check OpenAI provider first (default)
        if self.openai_provider.supports_model(model):
            return self.openai_provider
        
        # Check XLM provider if available
        if self.xlm_provider and self.xlm_provider.supports_model(model):
            return self.xlm_provider
        
        # Model not supported by any provider
        supported_models = self.get_supported_models()
        raise ValueError(
            f"Model '{model}' not supported. "
            f"Supported models: {', '.join(supported_models)}"
        )
        
        return self.openai_provider
    
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
            model: Model name (defaults to GPT-5)
            tools: Optional list of tools/functions
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            ChatCompletionResponse: Response object
        """
        target_model = model or self.default_model
        provider = self.get_provider_for_model(target_model)
        
        # For OpenAI models, call provider directly to avoid validation issues
        if target_model == ModelType.GPT_5:
            # Filter out GLM-specific parameters and None values
            openai_kwargs = {
                k: v for k, v in kwargs.items() 
                if k not in ['thinking', 'do_sample', 'user_id', 'request_id'] and v is not None
            }
            
            # Map 'reasoning' to 'reasoning_effort' for OpenAI
            if 'reasoning' in kwargs and kwargs['reasoning'] is not None:
                openai_kwargs['reasoning_effort'] = kwargs['reasoning']
            
            # Add standard parameters, only if they're not None
            if kwargs.get('temperature') is not None:
                openai_kwargs['temperature'] = kwargs.get('temperature', 0.7)
            if kwargs.get('top_p') is not None:
                openai_kwargs['top_p'] = kwargs.get('top_p', 1.0)
            if kwargs.get('max_tokens') is not None:
                openai_kwargs['max_tokens'] = kwargs.get('max_tokens')
            if kwargs.get('stream') is not None:
                openai_kwargs['stream'] = kwargs.get('stream', False)
            
            # Convert tools to OpenAI format if provided
            openai_tools = None
            if tools:
                from app.tools.registry import tool_registry
                # Get tools in standard nested format for chat completions API
                openai_tools = tool_registry.to_openai_format()
                
            return provider.create_completion(
                messages=messages,
                model=target_model,
                tools=openai_tools,
                **openai_kwargs
            )
        
        # For GLM models, use the existing request validation
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
        Check if any provider supports the given model.
        
        Args:
            model: Model name to check
            
        Returns:
            bool: True if the model is supported
        """
        if self.openai_provider.supports_model(model):
            return True
        if self.xlm_provider and self.xlm_provider.supports_model(model):
            return True
        return False
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models from all providers.
        
        Returns:
            List[str]: List of supported model names
        """
        models = list(self.openai_provider.get_supported_models())
        if self.xlm_provider:
            models.extend(self.xlm_provider.get_supported_models())
        return models
    
    def get_default_model(self) -> str:
        """
        Get the default model (GPT-5).
        
        Returns:
            str: Default model name
        """
        return self.default_model
