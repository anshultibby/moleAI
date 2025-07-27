import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from ..config import GEMINI_API_KEY
from ..tools import Tool
from ..tools.execution import process_tool_response


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

    def _build_tool_prompt(self) -> str:
        """Build tool prompt"""
        tool_descriptions = []
        for tool in self.tools.values():
            desc = f"- {tool.name}: {tool.description}"
            if tool.parameters:
                desc += f"\n  Parameters: {json.dumps(tool.parameters, indent=2)}"
            tool_descriptions.append(desc)
        return "\n".join(tool_descriptions)


    def _build_system_instructions(self) -> str:
        """Build system instructions including tool descriptions"""

        tool_prompt = self._build_tool_prompt()
        system_prompt = f"""
You are an expert shopping assistant. You help users find products on the internet 
and display them according to their preferences and requirements.

You have the following tools available to do this:
{tool_prompt}

The ui you operate in as follows:
there are two sections on the page. Left side is the chat window, right side is a display of products that get populated slowly.
When you call the add_product tool, the product will be displayed on the right side.
So you have two ways to communicate with the user. Via text on the chat window and via product cards in the right side.

Guidelines:
1. To help users find products: use find_stores to discover relevant stores, then fetch_products to get product data
2. To display products to users: use add_product for each specific item you want to show them
3. When using tools, respond with the following JSON format:
{{
    "tool_calls": [
        {{"name": "tool_name", "arguments": {{"param1": "value1"}}}},
        {{"name": "tool_name2", "arguments": {{"param2": "value2"}}}}
    ]
}}
4. When replying to user use conversational language and be friendly and helpful.
5. In the reply to the user dont reiterate what you have found if you showed it using add product.
5. Make sure all products you find will match what user is looking for, we wanna avoid false positives.
6. Since you have a mechanism to display intermediate results to the user, you can go on for a bit longer and keep searching. 
The user will be engaaged looking at the initial results and will be more patient even if you were to take a while.
7. You can always search for new stores with a variation of the query or get more items from the stores you have found.
"""
        return system_prompt

    def run_conversation(self, user_message: str = None, conversation_history: List[Dict[str, str]] = None, max_iterations: int = 40) -> List[Dict[str, str]]:
        """
        Run the conversation with existing history or start a new one.
        
        Args:
            user_message: New user message (required for new conversations)
            conversation_history: Existing conversation history (optional)
            max_iterations: Maximum number of iterations for tool calling
            
        Returns:
            List of all messages in the conversation
        """
        print(f"\n🔄 Starting conversation (max {max_iterations} iterations)...")
        
        # Initialize messages with existing history or create new conversation
        if conversation_history:
            # Use existing history - it should already include system message and all previous messages
            messages = conversation_history.copy()
            print(f"📚 Using existing history with {len(messages)} messages")
            
            # Add new user message if provided
            if user_message:
                messages.append({"role": "user", "content": user_message})
                print(f"➕ Added new user message")
        else:
            # New conversation - start with system message and user message
            if not user_message:
                raise ValueError("user_message is required for new conversations")
            messages = [
                {"role": "system", "content": self.system_instructions},
                {"role": "user", "content": user_message}
            ]
            print(f"🆕 Created new conversation")
        
        for iteration in range(max_iterations):
            print(f"\n🔄 Iteration {iteration + 1}/{max_iterations}")

            response = self.llm.chat_completion(messages)
            
            # Try to process as tool calls
            tool_messages = process_tool_response(response, self.tools)
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
                # Regular assistant message - add to history and end conversation
                print("💬 No tool calls found, treating as regular assistant message")
                messages.append({"role": "assistant", "content": response})
                break
            
        print(f"\n✅ Conversation complete with {len(messages)} total messages")
        return messages

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