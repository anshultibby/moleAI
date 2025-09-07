from typing import List, Optional, Generator, Dict, Any, Callable
from openai import OpenAI
import json
from app.models import (
    OpenAIRequest, 
    ToolCall, 
    ToolCallOutput, 
    Message, 
    InputMessage,
    Tool,
    ReasoningConfig,
    ThinkingResponse,
    ToolCallsResponse,
    AssistantResponse,
    AgentResponse
)


class Agent:
    def __init__(self, 
                 system_prompt: str, 
                 model: str, 
                 tools: Optional[List[Tool]] = None,
                 reasoning_effort: str = "medium",
                 api_key: Optional[str] = None,
                 tool_functions: Optional[Dict[str, Callable]] = None):
        self.system_prompt = system_prompt
        self.model = model
        self.tools = tools or []
        self.reasoning_effort = reasoning_effort
        self.message_history: List[InputMessage] = []
        self.client = OpenAI(api_key=api_key)
        self.tool_functions = tool_functions or {}
        
        # Add system message to history
        system_message = Message(
            role="system", 
            content=self.system_prompt
        )
        self.message_history.append(system_message)

    def step(self, input_message: InputMessage):
        """Add an input message and call the OpenAI responses API"""
        self.message_history.append(input_message)
        
        # Convert models to dict format for API call
        input_data = []
        for msg in self.message_history:
            input_data.append(msg.dict())
        
        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "input": input_data
        }
        
        if self.tools:
            api_params["tools"] = [tool.dict() for tool in self.tools]
            
        if self.reasoning_effort:
            api_params["reasoning"] = {"effort": self.reasoning_effort}
        
        # Call OpenAI responses API
        response = self.client.responses.create(**api_params)
        
        return response
        
    
    def add_to_history(self, message: InputMessage):
        """Add a message to the conversation history"""
        self.message_history.append(message)
    
    def execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a tool call and return the result"""
        if tool_call.name not in self.tool_functions:
            return f"Error: Tool '{tool_call.name}' not found"
        
        try:
            # Parse arguments and call the function
            args = tool_call.parse_arguments()
            result = self.tool_functions[tool_call.name](**args)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_call.name}: {str(e)}"
    
    def run(self, initial_message: InputMessage) -> Generator[AgentResponse, InputMessage, None]:
        """
        Run the conversation loop. Yields responses and waits for user input.
        
        Yields:
        - Assistant responses when conversation stops
        - Tool call information when tools are being executed
        
        Sends:
        - User input messages to continue the conversation
        """
        current_message = initial_message
        
        while True:
            # Call OpenAI API
            response = self.step(current_message)
            
            # First, yield any thinking/reasoning content
            if hasattr(response, 'output') and response.output:
                for output_item in response.output:
                    if hasattr(output_item, 'type') and output_item.type == "reasoning":
                        yield ThinkingResponse(
                            content=output_item.content if hasattr(output_item, 'content') else [str(output_item)],
                            summary=output_item.summary if hasattr(output_item, 'summary') else None,
                            response=response
                        )
            
            # Check if response has tool calls
            has_tool_calls = False
            tool_calls = []
            tool_outputs = []
            
            if hasattr(response, 'output') and response.output:
                for output_item in response.output:
                    if hasattr(output_item, 'type') and output_item.type == "function_call":
                        has_tool_calls = True
                        
                        # Create ToolCall object
                        tool_call = ToolCall(
                            id=output_item.id,
                            call_id=output_item.call_id,
                            name=output_item.name,
                            arguments=output_item.arguments
                        )
                        
                        # Execute the tool call
                        result = self.execute_tool_call(tool_call)
                        
                        # Create tool call output
                        tool_output = ToolCallOutput(
                            call_id=tool_call.call_id,
                            output=result
                        )
                        
                        # Add both tool call and output to history
                        self.add_to_history(tool_call)
                        self.add_to_history(tool_output)
                        
                        # Collect both calls and outputs
                        tool_calls.append(tool_call)
                        tool_outputs.append(tool_output)
            
            if has_tool_calls:
                # Yield both tool calls and their results
                yield ToolCallsResponse(
                    tool_calls=tool_calls,
                    tool_outputs=tool_outputs,
                    response=response
                )
                
                # Continue with empty message to get next response
                current_message = None
                
            else:
                # No tool calls - yield the response and wait for user input
                yield AssistantResponse(response=response)
                
                # Wait for next user input
                current_message = yield
                
                if current_message is None:
                    break
    
    def get_message_history(self) -> List[InputMessage]:
        return self.message_history.copy()
    
    def get_system_prompt(self) -> str:
        return self.system_prompt