"""
LLM Router for routing requests to appropriate providers.

This module provides a router that automatically selects the correct LLM provider
based on the model name and routes requests accordingly.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .xlm_provider import XLMProvider
from app.models.chat import InputMessage, OpenAIResponse


class LLMRouter:
    """Router that routes LLM requests to the appropriate provider based on model name."""
    
    def __init__(self, openai_api_key: Optional[str] = None, xlm_api_key: Optional[str] = None):
        """
        Initialize the LLM router with API keys for different providers.
        
        Args:
            openai_api_key: OpenAI API key
            xlm_api_key: XLM (Z.AI) API key
        """
        self.providers: Dict[str, BaseLLMProvider] = {}
        
        # Initialize OpenAI provider if API key is provided
        if openai_api_key:
            self.providers['openai'] = OpenAIProvider(openai_api_key)
        
        # Initialize XLM provider if API key is provided
        if xlm_api_key:
            self.providers['xlm'] = XLMProvider(xlm_api_key)
        
        if not self.providers:
            logger.warning("No LLM providers initialized - no API keys provided")
    
    def get_provider_for_model(self, model: str) -> BaseLLMProvider:
        """
        Get the appropriate provider for the given model.
        
        Args:
            model: Model name to route
            
        Returns:
            BaseLLMProvider: The provider that supports this model
            
        Raises:
            ValueError: If no provider supports the model
        """
        for _provider_name, provider in self.providers.items():
            if provider.supports_model(model):
                return provider
        
        # If no provider found, list available models
        available_models = self.get_all_supported_models()
        raise ValueError(
            f"No provider supports model '{model}'. "
            f"Available models: {', '.join(available_models)}"
        )
    
    def create_completion(
        self,
        messages: List[InputMessage],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> OpenAIResponse:
        """
        Create a chat completion by routing to the appropriate provider.
        
        Args:
            messages: List of conversation messages
            model: Model name to use
            tools: Optional list of tools/functions
            reasoning: Optional reasoning configuration
            **kwargs: Additional model-specific parameters
            
        Returns:
            OpenAIResponse: Standardized response object
        """
        provider = self.get_provider_for_model(model)
        return provider.create_completion(
            messages=messages,
            model=model,
            tools=tools,
            reasoning=reasoning,
            **kwargs
        )
    
    def supports_model(self, model: str) -> bool:
        """
        Check if any provider supports the given model.
        
        Args:
            model: Model name to check
            
        Returns:
            bool: True if any provider supports the model
        """
        return any(provider.supports_model(model) for provider in self.providers.values())
    
    def get_all_supported_models(self) -> List[str]:
        """
        Get list of all models supported by all providers.
        
        Returns:
            List[str]: List of all supported model names
        """
        all_models = []
        for provider in self.providers.values():
            all_models.extend(provider.get_supported_models())
        return sorted(list(set(all_models)))  # Remove duplicates and sort
    
    def get_provider_info(self) -> Dict[str, List[str]]:
        """
        Get information about available providers and their supported models.
        
        Returns:
            Dict[str, List[str]]: Mapping of provider names to their supported models
        """
        info = {}
        for provider_name, provider in self.providers.items():
            info[provider_name] = provider.get_supported_models()
        return info
    
    def add_provider(self, name: str, provider: BaseLLMProvider):
        """
        Add a new provider to the router.
        
        Args:
            name: Name for the provider
            provider: Provider instance
        """
        self.providers[name] = provider
        logger.info(f"Added {name} provider with models: {provider.get_supported_models()}")
    
    def remove_provider(self, name: str):
        """
        Remove a provider from the router.
        
        Args:
            name: Name of the provider to remove
        """
        if name in self.providers:
            del self.providers[name]
            logger.info(f"Removed {name} provider")
        else:
            logger.warning(f"Provider {name} not found")
