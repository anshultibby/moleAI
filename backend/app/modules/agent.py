import json
import re
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
import google.generativeai as genai


@dataclass
class Tool:
    """A function that can be called by the agent"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any] = None
    
    def call(self, **kwargs) -> str:
        """Execute the tool function with given arguments"""
        try:
            if self.parameters:
                # Validate parameters if defined
                for param, config in self.parameters.items():
                    if config.get('required', False) and param not in kwargs:
                        raise ValueError(f"Required parameter '{param}' missing")
            
            result = self.function(**kwargs)
            return str(result) if result is not None else "Function executed successfully"
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}"


class LLM:
    """Base LLM interface for chat completions"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key
        self._setup_client()
    
    def _setup_client(self):
        """Setup the LLM client"""
        if "gemini" in self.model_name.lower():
            if self.api_key:
                genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            self.client_type = "gemini"
        else:
            # Could add other LLM providers here
            raise ValueError(f"Unsupported model: {self.model_name}")
    
    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Get chat completion from the LLM"""
        try:
            if self.client_type == "gemini":
                # Convert messages to Gemini format
                conversation_text = self._format_messages_for_gemini(messages)
                response = self.client.generate_content(conversation_text)
                return response.text
            else:
                raise ValueError(f"Unsupported client type: {self.client_type}")
        except Exception as e:
            return f"Error getting LLM response: {str(e)}"
    
    def _format_messages_for_gemini(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Gemini API"""
        formatted = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                formatted.append(f"SYSTEM: {content}")
            elif role == 'user':
                formatted.append(f"USER: {content}")
            elif role == 'assistant':
                formatted.append(f"ASSISTANT: {content}")
            elif role == 'function':
                formatted.append(f"FUNCTION_RESULT: {content}")
        return "\n\n".join(formatted)


@dataclass
class ToolCall:
    """Represents a tool call extracted from LLM response"""
    name: str
    arguments: Dict[str, Any]
    call_id: str = None


class Agent:
    def __init__(self, name: str, description: str, tools: List[Tool], llm: LLM):
        self.name = name
        self.description = description
        self.tools = {tool.name: tool for tool in tools}
        self.llm = llm
        self.system_instructions = self._build_system_instructions()

    def _build_system_instructions(self) -> str:
        """Build system instructions including tool descriptions"""
        instructions = f"""You are {self.name}: {self.description}

Available tools:
"""
        for tool in self.tools.values():
            instructions += f"- {tool.name}: {tool.description}\n"
            if tool.parameters:
                instructions += f"  Parameters: {json.dumps(tool.parameters, indent=2)}\n"
        
        instructions += """
When you want to use a tool, respond with a JSON object in this format:
{
    "tool_call": {
        "name": "tool_name",
        "arguments": {"param1": "value1", "param2": "value2"}
    }
}

When you want to send a message to the user, respond with plain text (no JSON).

You can either:
1. Call a tool (which will be executed and results added to conversation)
2. Send a message to the user (which will be displayed)

Always be helpful and use tools when appropriate to assist the user.
"""
        return instructions

    def get_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Get chat completion with system instructions"""
        # Add system instructions as first message if not present
        messages_with_system = []
        if not messages or messages[0].get('role') != 'system':
            messages_with_system.append({
                'role': 'system', 
                'content': self.system_instructions
            })
        messages_with_system.extend(messages)
        
        return self.llm.chat_completion(messages_with_system)

    def _extract_tool_call(self, response: str) -> Optional[ToolCall]:
        """Extract tool call from LLM response"""
        try:
            # Look for JSON in the response
            lines = response.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        data = json.loads(line)
                        if 'tool_call' in data:
                            tool_data = data['tool_call']
                            return ToolCall(
                                name=tool_data['name'],
                                arguments=tool_data.get('arguments', {}),
                                call_id=f"call_{len(response)}"
                            )
                    except json.JSONDecodeError:
                        continue
            
            # Also check if the entire response is JSON
            try:
                data = json.loads(response.strip())
                if 'tool_call' in data:
                    tool_data = data['tool_call']
                    return ToolCall(
                        name=tool_data['name'],
                        arguments=tool_data.get('arguments', {}),
                        call_id=f"call_{len(response)}"
                    )
            except json.JSONDecodeError:
                pass
                
        except Exception as e:
            print(f"Error extracting tool call: {e}")
        
        return None

    def run_conversation(self, user_message: str, max_iterations: int = 10) -> List[Dict[str, Any]]:
        """
        Run the agentic conversation loop
        Returns list of conversation messages including tool calls and results
        """
        conversation = []
        
        # Add user message
        conversation.append({
            'role': 'user',
            'content': user_message,
            'type': 'message'
        })
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Get LLM response
            llm_response = self.get_chat_completion([
                {k: v for k, v in msg.items() if k in ['role', 'content']} 
                for msg in conversation
            ])
            
            # Check if this is a tool call or assistant message
            tool_call = self._extract_tool_call(llm_response)
            
            if tool_call:
                # Add tool call to conversation
                conversation.append({
                    'role': 'assistant',
                    'content': llm_response,
                    'type': 'tool_call',
                    'tool_call': {
                        'name': tool_call.name,
                        'arguments': tool_call.arguments,
                        'call_id': tool_call.call_id
                    }
                })
                
                # Execute the tool
                if tool_call.name in self.tools:
                    tool = self.tools[tool_call.name]
                    result = tool.call(**tool_call.arguments)
                    
                    # Add tool result to conversation
                    conversation.append({
                        'role': 'function',
                        'content': result,
                        'type': 'tool_result',
                        'tool_call_id': tool_call.call_id,
                        'tool_name': tool_call.name
                    })
                else:
                    # Tool not found
                    conversation.append({
                        'role': 'function',
                        'content': f"Error: Tool '{tool_call.name}' not found",
                        'type': 'tool_result',
                        'tool_call_id': tool_call.call_id,
                        'tool_name': tool_call.name
                    })
                
                # Continue the loop to get next response
                continue
            else:
                # This is a regular assistant message - conversation ends
                conversation.append({
                    'role': 'assistant',
                    'content': llm_response,
                    'type': 'message'
                })
                break
        
        return conversation

    def add_tool(self, tool: Tool):
        """Add a new tool to the agent"""
        self.tools[tool.name] = tool
        self.system_instructions = self._build_system_instructions()

    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.system_instructions = self._build_system_instructions()