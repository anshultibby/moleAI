# Models module - Define your data models here
from .chat import (
    TextContent,
    ImageContent,
    Message, 
    Tool, 
    ToolCall, 
    ToolCallOutput,
    ForcedFunctionChoice,
    AllowedToolRef,
    AllowedToolsChoice,
    ToolChoice,
    OpenAIRequest,
    ReasoningConfig,
    ReasoningOutput,
    ThinkingResponse,
    ToolCallsResponse,
    AssistantResponse,
    AgentResponse,
    InputMessage,
    OpenAIResponse,
    OpenAIResponseBase,
    ResponseOutputItem,
    ResponseReasoningItem,
    ResponseOutputMessage,
    ResponseOutputText
)

from .search_models import (
    TokenUsage,
    SearchMetadata,
    PageMetadata,
    ExternalResources,
    SearchResult,
    JinaSearchResponse,
    SearchSummary,
    parse_search_response,
    load_search_response_from_file
)

__all__ = [
    # Chat models
    "TextContent",
    "ImageContent", 
    "Message", 
    "Tool", 
    "ToolCall", 
    "ToolCallOutput",
    "ForcedFunctionChoice",
    "AllowedToolRef", 
    "AllowedToolsChoice",
    "ToolChoice",
    "OpenAIRequest",
    "ReasoningConfig",
    "ReasoningOutput",
    "ThinkingResponse",
    "ToolCallsResponse", 
    "AssistantResponse",
    "AgentResponse",
    "InputMessage",
    "OpenAIResponse",
    "OpenAIResponseBase",
    "ResponseOutputItem",
    "ResponseReasoningItem", 
    "ResponseOutputMessage",
    "ResponseOutputText",
    
    # Search models
    "TokenUsage",
    "SearchMetadata",
    "PageMetadata",
    "ExternalResources",
    "SearchResult",
    "JinaSearchResponse",
    "SearchSummary",
    "parse_search_response",
    "load_search_response_from_file"
]
