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

# Type alias for input messages
InputMessage = Union[Message, ToolCall, ToolCallOutput, ReasoningOutput]

# OpenAI Responses Request (for responses.create API)
class OpenAIRequest(BaseModel):
    model: str
    input: List[InputMessage]
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[ToolChoice] = "auto"
    reasoning: Optional[ReasoningConfig] = None
