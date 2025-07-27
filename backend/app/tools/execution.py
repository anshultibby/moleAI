"""Tool execution logic extracted from agent module"""

import json
from typing import List, Dict, Any, Optional
from .base import Tool, ToolCall, ToolCallList


def extract_tool_calls_from_response(response: str) -> Optional[ToolCallList]:
    """
    Extract and validate tool calls from LLM response.
    Returns ToolCallList if valid tool calls found, otherwise None.
    """
    try:
        print(f"🔍 Checking response for JSON block...")
        if "{" in response:
            # Extract JSON from code block
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            print(f"📦 Found JSON: {json_str[:200]}...")
                    
            tool_calls = ToolCallList.model_validate_json(json_str)
            print(f"✓ Validated {len(tool_calls.tool_calls)} tool calls")
            return tool_calls
            
        else:
            print("❌ No JSON found in response")
    except Exception as e:
        print(f"❌ Error extracting tool calls: {str(e)}")
    return None


def execute_tool_calls(tool_calls: ToolCallList, available_tools: Dict[str, Tool]) -> List[Dict[str, str]]:
    """
    Execute validated tool calls and return formatted messages.
    Returns list of messages containing tool results.
    """
    messages = []
    
    # Execute each tool in sequence
    for tool_call in tool_calls.tool_calls:
        print(f"\n🛠️  Executing tool: {tool_call.name}")
        print(f"Arguments: {tool_call.arguments}")
        
        if tool_call.name in available_tools:
            tool = available_tools[tool_call.name]
            result = tool.call(**tool_call.arguments)
            print(f"Result: {result[:200]}...")
            messages.append({"role": "tool_result", "content": result})
        else:
            print(f"❌ Tool {tool_call.name} not found!")
            error_msg = f"Error: Tool '{tool_call.name}' not found in available tools"
            messages.append({"role": "tool_result", "content": error_msg})
    
    return messages


def process_tool_response(response: str, available_tools: Dict[str, Tool]) -> Optional[List[Dict[str, str]]]:
    """
    Main function to extract tool calls from response, validate and execute them.
    Returns list of messages (tool calls and results) if valid tool calls found,
    otherwise returns None.
    
    This is the main public function that replaces Agent._execute_tool_calls().
    """
    try:
        # Extract tool calls from response
        tool_calls = extract_tool_calls_from_response(response)
        if not tool_calls:
            return None
        
        messages = []
        # Add the tool calls response
        messages.append({"role": "tool", "content": response})
        
        # Execute the tool calls
        tool_results = execute_tool_calls(tool_calls, available_tools)
        messages.extend(tool_results)
        
        return messages
        
    except Exception as e:
        print(f"❌ Error processing tool response: {str(e)}")
        return None 