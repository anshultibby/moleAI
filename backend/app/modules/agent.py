import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from pydantic import BaseModel
import google.generativeai as genai

from ..config import GEMINI_API_KEY


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolCallList(BaseModel):
    tool_calls: List[ToolCall]


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
        print(f"\n🤖 Initializing LLM with model: {model_name}")
        self.model_name = model_name
        self.api_key = api_key
        self._setup_client()
    
    def _setup_client(self):
        """Setup the LLM client"""
        if "gemini" in self.model_name.lower():
            if self.api_key:
                print("✓ Configuring Gemini with API key")
                genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            self.client_type = "gemini"
            print("✓ Gemini client ready")
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")
    
    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Get chat completion from the LLM"""
        try:
            if self.client_type == "gemini":
                print("\n📤 Preparing Gemini request...")
                conversation_text = "\n\n".join([
                    f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
                    for msg in messages
                ])
                print(f"📝 First 200 chars of conversation: {conversation_text[:200]}...")
                
                print("🚀 Sending to Gemini...")
                response = self.client.generate_content(conversation_text)
                print(f"📥 Got response: {response.text[:200]}...")
                return response.text
        except Exception as e:
            print(f"❌ Error in LLM: {str(e)}")
            return f"Error getting LLM response: {str(e)}"


class Agent:
    """Core Agent class that handles tool-based conversations with LLMs"""
    
    def __init__(self, name: str, description: str, tools: List[Tool], llm: LLM):
        self.name = name
        self.description = description
        self.tools = {tool.name: tool for tool in tools}
        self.llm = llm
        self.system_instructions = self._build_system_instructions()

    def _build_system_instructions(self) -> str:
        """Build system instructions including tool descriptions"""
        tool_descriptions = []
        for tool in self.tools.values():
            desc = f"- {tool.name}: {tool.description}"
            if tool.parameters:
                desc += f"\n  Parameters: {json.dumps(tool.parameters, indent=2)}"
            tool_descriptions.append(desc)

        return f"""You are {self.name}: {self.description}

Available tools:
{chr(10).join(tool_descriptions)}

When using tools, respond with the following JSON format:
{{
    "tool_calls": [
        {{"name": "tool_name", "arguments": {{"param1": "value1"}}}},
        {{"name": "tool_name2", "arguments": {{"param2": "value2"}}}}
    ]
}}
"""

    def run_conversation(self, user_message: str, max_iterations: int = 10) -> List[Dict[str, str]]:
        """Run the conversation and return the message history"""
        print(f"\n🔄 Starting new conversation (max {max_iterations} iterations)...")
        messages = [
            {"role": "system", "content": self.system_instructions},
            {"role": "user", "content": user_message}
        ]
        print(f"📝 System instructions length: {len(self.system_instructions)}")
        
        for iteration in range(max_iterations):
            print(f"\n📍 Iteration {iteration + 1}/{max_iterations}:")
            
            # Get LLM response
            print("🤖 Getting LLM response...")
            response = self.llm.chat_completion(messages)
            print(f"📤 LLM response: {response[:200]}...")
            
            # Try to execute tool calls
            print("🔍 Looking for tool calls...")
            tool_messages = self._execute_tool_calls(response)
            if tool_messages:
                print(f"🛠️  Found and executed {len(tool_messages)} tool messages")
                messages.extend(tool_messages)
                
                if iteration == max_iterations - 1:
                    print("⚠️ Hit max iterations with tool calls pending")
                    # Add a final message explaining we hit the limit
                    messages.append({
                        "role": "assistant",
                        "content": "I apologize, but I've hit the maximum number of conversation turns. Let me summarize what I found so far..."
                    })
                else:
                    continue
            else:
                # Regular message - add to history and end conversation
                print("💬 No tool calls found, treating as regular message")
                messages.append({"role": "assistant", "content": response})
                break
            
        print(f"\n✅ Conversation complete with {len(messages)} total messages")
        return messages

    def _execute_tool_calls(self, response: str) -> Optional[List[Dict[str, str]]]:
        """
        Extract tool calls from response, validate and execute them.
        Returns list of messages (tool calls and results) if valid tool calls found,
        otherwise returns None.
        """
        try:
            print(f"🔍 Checking response for JSON block...")
            if "```json" in response:
                # Extract JSON from code block
                parts = response.split("```")
                for part in parts:
                    if part.strip().startswith("json"):
                        json_str = part.replace("json", "").strip()
                        print(f"📦 Found JSON: {json_str[:200]}...")
                        
                        tool_calls = ToolCallList.model_validate_json(json_str)
                        print(f"✓ Validated {len(tool_calls.tool_calls)} tool calls")
                        
                        messages = []
                        # Add the tool calls response
                        messages.append({"role": "assistant", "content": response})
                        
                        # Execute each tool in sequence
                        for tool_call in tool_calls.tool_calls:
                            print(f"\n🛠️  Executing tool: {tool_call.name}")
                            print(f"Arguments: {tool_call.arguments}")
                            
                            if tool_call.name in self.tools:
                                tool = self.tools[tool_call.name]
                                result = tool.call(**tool_call.arguments)
                                print(f"Result: {result[:200]}...")
                                messages.append({"role": "function", "content": result})
                            else:
                                print(f"❌ Tool {tool_call.name} not found!")
                        
                        return messages
                
                print("❌ No valid JSON found in code blocks")
            else:
                print("❌ No ```json block found in response")
        except Exception as e:
            print(f"❌ Error executing tool calls: {str(e)}")
        return None

    def add_tool(self, tool: Tool):
        """Add a new tool to the agent"""
        self.tools[tool.name] = tool
        self.system_instructions = self._build_system_instructions()

    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.system_instructions = self._build_system_instructions()
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.tools.keys())
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if agent has a specific tool"""
        return tool_name in self.tools
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            return {
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.parameters
            }
        return None