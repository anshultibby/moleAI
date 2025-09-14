"""
Base LLM provider interface.

This module defines the abstract base class that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models.chat import InputMessage, ChatCompletionResponse


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def create_completion(
        self,
        messages: List[InputMessage],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        Create a chat completion.
        
        Args:
            messages: List of conversation messages
            model: Model name to use
            tools: Optional list of tools/functions available to the model
            reasoning: Optional reasoning configuration
            **kwargs: Additional model-specific parameters
            
        Returns:
            ChatCompletionResponse: Standardized response object
        """
        pass
    
    def supports_model(self, model: str) -> bool:
        """
        Check if this provider supports the given model.
        
        Args:
            model: Model name to check
            
        Returns:
            bool: True if the model is supported by this provider
        """
        return model in self.SUPPORTED_MODELS
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of models supported by this provider.
        
        Returns:
            List[str]: List of supported model names
        """
        return self.SUPPORTED_MODELS.copy()
    
    def format_messages_for_api(self, messages: List[InputMessage]) -> List[Dict[str, Any]]:
        """
        Convert InputMessage objects to API format.
        
        Args:
            messages: List of InputMessage objects
            
        Returns:
            List[Dict[str, Any]]: Messages formatted for API call
        """
        formatted_messages = []
        for msg in messages:
            if msg is not None:
                formatted_messages.append(msg.dict())
        return formatted_messages
    
    def format_tools_for_api(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        Format tools for the specific provider's API.
        
        Args:
            tools: List of tool definitions
            
        Returns:
            Optional[List[Dict[str, Any]]]: Tools formatted for API call
        """
        if not tools:
            return None
        return tools
