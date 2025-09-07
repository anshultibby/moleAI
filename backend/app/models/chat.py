from pydantic import BaseModel
from typing import Literal, Dict, Any, Optional, List, Union
import json

class TextContent(BaseModel):
    type: Literal["input_text"] = "input_text"
    text: str

class ImageContent(BaseModel):
    type: Literal["input_image"] = "input_image"
    image_url: str

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: Union[str, List[Union[TextContent, ImageContent]]]

class Tool(BaseModel):
    type: Literal["function"] = "function"
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: Optional[bool] = None   

class ToolCall(BaseModel):
    id: str
    call_id: str
    type: Literal["function_call"] = "function_call"
    name: str
    arguments: str

    def parse_arguments(self) -> Dict[str, Any]:
        return json.loads(self.arguments)

class ToolCallOutput(BaseModel):
    type: Literal["function_call_output"] = "function_call_output"
    call_id: str
    output: str

# Tool Choice Models
class ForcedFunctionChoice(BaseModel):
    type: Literal["function"] = "function"
    name: str

class AllowedToolRef(BaseModel):
    type: Literal["function", "mcp", "image_generation"]
    name: Optional[str] = None  # For function type
    server_label: Optional[str] = None  # For mcp type

class AllowedToolsChoice(BaseModel):
    type: Literal["allowed_tools"] = "allowed_tools"
    mode: Literal["auto", "required"] = "auto"
    tools: List[AllowedToolRef]

# Union type for all tool choice options
ToolChoice = Union[
    Literal["auto", "required"],  # Simple string choices
    ForcedFunctionChoice,         # Force specific function
    AllowedToolsChoice           # Allowed tools with restrictions
]

# OpenAI Response Request Models (for responses.create)
class ReasoningConfig(BaseModel):
    effort: Literal["low", "medium", "high"] = "low"

# Reasoning/Thinking output models
class ReasoningOutput(BaseModel):
    id: str
    type: Literal["reasoning"] = "reasoning"
    content: List[str] = []
    summary: List[str] = []

# Agent Response Models (for yielding from run method)
class ThinkingResponse(BaseModel):
    type: Literal["thinking"] = "thinking"
    content: List[str]
    summary: Optional[List[str]] = None
    response: Any  # Full OpenAI response object

class ToolCallsResponse(BaseModel):
    type: Literal["tool_calls"] = "tool_calls"
    tool_calls: List[ToolCall]
    tool_outputs: List[ToolCallOutput]
    response: Any  # Full OpenAI response object

class AssistantResponse(BaseModel):
    type: Literal["assistant_response"] = "assistant_response"
    response: Any  # Full OpenAI response object

# Union type for all agent responses
AgentResponse = Union[ThinkingResponse, ToolCallsResponse, AssistantResponse]

# OpenAI Response Models (based on actual API response structure)
class ResponseOutputText(BaseModel):
    annotations: List[Any] = []
    text: str
    type: Literal["output_text"] = "output_text"
    logprobs: List[Any] = []

class ResponseOutputMessage(BaseModel):
    id: str
    content: List[ResponseOutputText]
    role: Literal["assistant"] = "assistant"
    status: Literal["completed"] = "completed"
    type: Literal["message"] = "message"

# Input-compatible versions (for sending to API)
class InputReasoningItem(BaseModel):
    id: str
    summary: List[str] = []
    type: Literal["reasoning"] = "reasoning"
    content: Optional[str] = None
    encrypted_content: Optional[str] = None

class InputFunctionToolCall(BaseModel):
    arguments: str
    call_id: str
    name: str
    type: Literal["function_call"] = "function_call"
    id: str

# Response versions (from API responses)
class ResponseReasoningItem(BaseModel):
    id: str
    summary: List[str] = []
    type: Literal["reasoning"] = "reasoning"
    content: Optional[str] = None
    encrypted_content: Optional[str] = None
    status: Optional[str] = None
    
    def to_input_format(self) -> "InputReasoningItem":
        """Convert to input-compatible format by removing status field"""
        return InputReasoningItem(
            id=self.id,
            summary=self.summary,
            type=self.type,
            content=self.content,
            encrypted_content=self.encrypted_content
        )

class ResponseFunctionToolCall(BaseModel):
    arguments: str
    call_id: str
    name: str
    type: Literal["function_call"] = "function_call"
    id: str
    status: str
    
    def to_input_format(self) -> "InputFunctionToolCall":
        """Convert to input-compatible format by removing status field"""
        return InputFunctionToolCall(
            arguments=self.arguments,
            call_id=self.call_id,
            name=self.name,
            type=self.type,
            id=self.id
        )

# Union type for all output items
ResponseOutputItem = Union[ResponseReasoningItem, ResponseOutputMessage, ResponseFunctionToolCall]

class InputTokensDetails(BaseModel):
    cached_tokens: int = 0

class OutputTokensDetails(BaseModel):
    reasoning_tokens: int = 0

class ResponseUsage(BaseModel):
    input_tokens: int
    input_tokens_details: InputTokensDetails
    output_tokens: int
    output_tokens_details: OutputTokensDetails
    total_tokens: int

class Reasoning(BaseModel):
    effort: str = "medium"
    generate_summary: Optional[bool] = None
    summary: Optional[str] = None

class OpenAIResponseBase(BaseModel):
    """Base model containing all the OpenAI response metadata fields"""
    id: str
    created_at: float
    error: Optional[Any] = None
    incomplete_details: Optional[Any] = None
    instructions: Optional[Any] = None
    metadata: Dict[str, Any] = {}
    model: str
    object: Literal["response"] = "response"
    parallel_tool_calls: bool = True
    temperature: float = 1.0
    tool_choice: str = "auto"
    tools: List[Any] = []
    top_p: float = 1.0
    background: bool = False
    conversation: Optional[Any] = None
    max_output_tokens: Optional[int] = None
    max_tool_calls: Optional[int] = None
    previous_response_id: Optional[str] = None
    prompt: Optional[Any] = None
    prompt_cache_key: Optional[str] = None
    reasoning: Optional[Reasoning] = None
    safety_identifier: Optional[str] = None
    service_tier: str = "default"
    status: Literal["completed"] = "completed"
    text: Optional[Any] = None
    top_logprobs: int = 0
    truncation: str = "disabled"
    usage: ResponseUsage
    user: Optional[str] = None
    store: bool = True

class OpenAIResponse(OpenAIResponseBase):
    """Clean OpenAI response model with just the essential output field"""
    output: List[ResponseOutputItem]

# Type alias for input messages (defined after all classes to avoid forward reference issues)
InputMessage = Union[Message, ToolCall, ToolCallOutput, ReasoningOutput, InputReasoningItem, InputFunctionToolCall]

# OpenAI Responses Request (for responses.create API)
class OpenAIRequest(BaseModel):
    model: str
    input: List[InputMessage]
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[ToolChoice] = "auto"
    reasoning: Optional[ReasoningConfig] = None
