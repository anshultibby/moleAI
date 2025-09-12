"""
Pydantic models for Z.AI (XLM) API requests and responses.

These models ensure type safety and proper validation for the Z.AI API.
"""

from typing import List, Dict, Any, Optional, Union, Literal, Annotated
from pydantic import BaseModel, Field
from loguru import logger


# Z.AI Message Models
class ZAITextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ZAIImageContent(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: Dict[str, str]  # {"url": "..."}


class ZAIVideoContent(BaseModel):
    type: Literal["video_url"] = "video_url"
    video_url: Dict[str, str]  # {"url": "..."}


class ZAIFileContent(BaseModel):
    type: Literal["file_url"] = "file_url"
    file_url: Dict[str, str]  # {"url": "..."}


# Union type for multimodal content
ZAIMultimodalContent = Union[ZAITextContent, ZAIImageContent, ZAIVideoContent, ZAIFileContent]


class ZAISystemMessage(BaseModel):
    role: Literal["system"] = "system"
    content: str


class ZAIUserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: Union[str, List[ZAIMultimodalContent]]  # Can be string OR multimodal array


# Tool call models with discriminated union
class ZAIFunctionToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: Dict[str, Any]


class ZAIWebSearchToolCall(BaseModel):
    id: str
    type: Literal["web_search"] = "web_search"
    web_search: Dict[str, Any]


class ZAIRetrievalToolCall(BaseModel):
    id: str
    type: Literal["retrieval"] = "retrieval"
    retrieval: Dict[str, Any]


# Discriminated union for tool calls
ZAIToolCall = Annotated[
    Union[ZAIFunctionToolCall, ZAIWebSearchToolCall, ZAIRetrievalToolCall],
    Field(discriminator='type')
]


class ZAIAssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = ""
    tool_calls: Optional[List[ZAIToolCall]] = None
    
    def model_post_init(self, __context) -> None:
        # If tool_calls are present, content should be empty per Z.AI API
        if self.tool_calls:
            self.content = ""


class ZAIToolMessage(BaseModel):
    role: Literal["tool"] = "tool"
    content: str
    tool_call_id: str


# Discriminated union for all message types (Pydantic will handle role-based routing)
ZAIMessage = Annotated[
    Union[ZAISystemMessage, ZAIUserMessage, ZAIAssistantMessage, ZAIToolMessage],
    Field(discriminator='role')
]


class ZAIThinking(BaseModel):
    type: Literal["enabled", "disabled"] = "enabled"


class ZAIResponseFormat(BaseModel):
    type: Literal["text", "json_object"] = "text"


class ZAIFunctionTool(BaseModel):
    type: Literal["function"] = "function"
    function: Dict[str, Any]


class ZAIWebSearchTool(BaseModel):
    type: Literal["web_search"] = "web_search"
    web_search: Dict[str, Any]


class ZAIRetrievalTool(BaseModel):
    type: Literal["retrieval"] = "retrieval"
    retrieval: Dict[str, Any]


# Discriminated union for tools (Pydantic will handle type-based routing)
ZAITool = Annotated[
    Union[ZAIFunctionTool, ZAIWebSearchTool, ZAIRetrievalTool],
    Field(discriminator='type')
]


class ZAIRequest(BaseModel):
    """Z.AI API request model"""
    model: str
    messages: List[ZAIMessage]
    request_id: Optional[str] = None
    do_sample: bool = True
    stream: bool = False
    thinking: Optional[ZAIThinking] = None
    temperature: float = Field(default=0.6, ge=0.0, le=1.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=24096, ge=1, le=98304)
    tools: Optional[List[ZAITool]] = None
    user_id: Optional[str] = Field(default=None, min_length=6, max_length=128)
    stop: Optional[List[str]] = Field(default=None, max_items=1)
    response_format: Optional[ZAIResponseFormat] = None


# Content conversion models
class ContentConverter(BaseModel):
    """Pydantic model to handle content conversion automatically"""
    
    @classmethod
    def prepare_content(cls, content: Any, role: str) -> Union[str, List[Dict[str, Any]]]:
        """Prepare content for Z.AI API based on role using Pydantic validation"""
        if role in ["system", "assistant", "tool"]:
            # These roles require string content
            return cls._extract_text_content(content)
        elif role == "user":
            # User messages can be string or multimodal
            if isinstance(content, str):
                return content
            else:
                # Try to convert to multimodal format using Pydantic
                try:
                    multimodal_items = []
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                # Let Pydantic handle the validation and routing
                                multimodal_item = ZAIMultimodalContent.model_validate(item)
                                multimodal_items.append(multimodal_item.model_dump())
                    return multimodal_items if multimodal_items else cls._extract_text_content(content)
                except Exception:
                    return cls._extract_text_content(content)
        else:
            return cls._extract_text_content(content)
    
    @staticmethod
    def _extract_text_content(content: Any) -> str:
        """Extract text content from various content formats."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return " ".join(text_parts) if text_parts else ""
        else:
            return str(content)


# Z.AI Response Models
class ZAIResponseUsage(BaseModel):
    """Z.AI API usage statistics"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ZAIResponseToolCall(BaseModel):
    """Z.AI tool call in response"""
    id: str
    type: Literal["function"] = "function"
    function: Dict[str, Any]


class ZAIResponseMessage(BaseModel):
    """Z.AI response message"""
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    tool_calls: Optional[List[ZAIResponseToolCall]] = None
    reasoning_content: Optional[str] = None


class ZAIResponseChoice(BaseModel):
    """Z.AI response choice"""
    index: int = 0
    message: ZAIResponseMessage
    finish_reason: Optional[str] = None


class ZAIResponse(BaseModel):
    """Complete Z.AI API response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ZAIResponseChoice]
    usage: ZAIResponseUsage


