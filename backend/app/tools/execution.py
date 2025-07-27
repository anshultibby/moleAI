"""Tool execution logic extracted from agent module"""

import json
from typing import List, Dict, Any, Optional, Tuple
from .base import Tool, ToolCall, ToolCallList


def extract_tool_calls_from_response(response: str) -> Tuple[Optional[str], Optional[ToolCallList]]:
    """
    Extract ephemeral text and tool calls from LLM response.
    Returns tuple of (ephemeral_text, tool_calls).
    ephemeral_text is any text before the first '{' character.
    tool_calls is ToolCallList if valid tool calls found, otherwise None.
    """
    ephemeral_text = None
    tool_calls = None
    
    try:
        print(f"🔍 Checking response for JSON blocks...")
        if "{" in response:
            # Extract text before the first '{'
            json_start = response.find("{")
            if json_start > 0:
                ephemeral_text = response[:json_start].strip()
                if ephemeral_text:
                    # Clean up ephemeral text
                    ephemeral_text = clean_ephemeral_text(ephemeral_text)
                    print(f"📝 Found ephemeral text: {ephemeral_text[:100]}...")
            
            # Try to find and parse complete JSON tool call blocks
            tool_calls = extract_tool_calls_from_json_blocks(response[json_start:])
            
        else:
            print("❌ No JSON found in response")
    except Exception as e:
        print(f"❌ Error extracting tool calls: {str(e)}")
    
    return ephemeral_text, tool_calls


def extract_tool_calls_from_json_blocks(json_text: str) -> Optional[ToolCallList]:
    """
    Extract tool calls from text that may contain multiple JSON blocks.
    Handles cases where there are multiple separate {"tool_calls": [...]} blocks.
    """
    import re
    import json
    
    all_tool_calls = []
    
    # Find all JSON-like blocks in the text
    brace_count = 0
    start_pos = None
    
    for i, char in enumerate(json_text):
        if char == '{':
            if brace_count == 0:
                start_pos = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_pos is not None:
                # Found a complete JSON block
                json_block = json_text[start_pos:i+1]
                try:
                    parsed = json.loads(json_block)
                    if isinstance(parsed, dict) and "tool_calls" in parsed:
                        # This is a valid tool calls block
                        for tool_call_data in parsed["tool_calls"]:
                            if "name" in tool_call_data and "arguments" in tool_call_data:
                                all_tool_calls.append(ToolCall(
                                    name=tool_call_data["name"],
                                    arguments=tool_call_data["arguments"]
                                ))
                        print(f"📦 Parsed {len(parsed['tool_calls'])} tool calls from JSON block")
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON block: {json_block[:100]}...")
                except Exception as e:
                    print(f"❌ Error parsing JSON block: {str(e)}")
    
    if all_tool_calls:
        print(f"✓ Total extracted: {len(all_tool_calls)} tool calls")
        return ToolCallList(tool_calls=all_tool_calls)
    else:
        print("❌ No valid tool calls found")
        return None


def clean_ephemeral_text(text: str) -> str:
    """
    Clean up ephemeral text by removing unwanted prefixes and patterns.
    """
    if not text:
        return text

    patterns_to_remove = [
        "TOOL_RESULT:",
        "TOOL_CALL:",
        "FUNCTION_CALL:",
        "TOOL:"
    ]
    
    for pattern in patterns_to_remove:
        if text.startswith(pattern):
            text = text[len(pattern):].strip()
    
    return text


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


def process_tool_response(response: str, available_tools: Dict[str, Tool]) -> Tuple[Optional[str], Optional[List[Dict[str, str]]]]:
    """
    Main function to extract ephemeral text and tool calls from response, validate and execute them.
    Returns tuple of (ephemeral_text, messages).
    ephemeral_text is text before tool calls that should be shown as ephemeral message.
    messages is list of messages (tool calls and results) if valid tool calls found, otherwise None.
    
    This is the main public function that replaces Agent._execute_tool_calls().
    """
    try:
        # Extract ephemeral text and tool calls from response
        ephemeral_text, tool_calls = extract_tool_calls_from_response(response)
        
        if not tool_calls:
            return ephemeral_text, None
        
        messages = []
        # Add the tool calls response
        messages.append({"role": "tool", "content": response})
        
        # Execute the tool calls
        tool_results = execute_tool_calls(tool_calls, available_tools)
        messages.extend(tool_results)
        
        return ephemeral_text, messages
        
    except Exception as e:
        print(f"❌ Error processing tool response: {str(e)}")
        return None, None 