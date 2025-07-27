import json
from typing import List, Dict, Any, Optional, Callable
import google.generativeai as genai

from ..config import GEMINI_API_KEY
from ..tools import Tool
from ..tools.execution import process_tool_response


class LLM:
    """Base LLM interface for chat completions"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: str = None):
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
                print(f"📥 Got response: {response}...")
                
                # Handle complex responses with multiple parts
                try:
                    # Try simple text accessor first
                    return response.text
                except ValueError as e:
                    # If response.text fails, extract text from parts
                    print(f"⚠️ Complex response detected, extracting from parts: {str(e)}")
                    if response.candidates and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if candidate.content and candidate.content.parts:
                            # Combine all text parts
                            text_parts = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                            if text_parts:
                                combined_text = ''.join(text_parts)
                                print(f"✓ Extracted text from {len(text_parts)} parts: {combined_text[:100]}...")
                                return combined_text
                    
                    # Fallback if we can't extract text
                    print(f"❌ Could not extract text from response: {response}")
                    return "Error: Could not extract text from complex response"
                
        except Exception as e:
            print(f"❌ Error in LLM: {str(e)}")
            return f"Error getting LLM response: {str(e)}"


class Agent:
    """Generic agent for managing conversation with LLM and tools"""
    
    def __init__(self, 
                 name: str, 
                 description: str, 
                 tools: List[Tool], 
                 llm: LLM,
                 base_system_prompt: str,
                 guidelines: str = ""):
        """
        Initialize the agent with tools and LLM
        
        Args:
            name: Agent name
            description: Agent description  
            tools: List of tools available to the agent
            llm: Language model instance
            base_system_prompt: The main system prompt describing the agent's role
            guidelines: Additional guidelines for the agent (optional)
        """
        self.name = name
        self.description = description
        self.tools = {tool.name: tool for tool in tools}
        self.llm = llm
        self.base_system_prompt = base_system_prompt
        self.guidelines = guidelines
        self.system_instructions = self._build_system_instructions()
        self.last_ephemeral_text: Optional[str] = None  # Store last ephemeral text found

    def _build_tool_prompt(self) -> str:
        """Build the prompt describing available tools"""
        if not self.tools:
            return "No tools available."

        tool_descriptions = []
        for tool in self.tools.values():
            # Build parameter descriptions
            param_desc = []
            if hasattr(tool, 'parameters') and tool.parameters:
                for param_name, param_info in tool.parameters.items():
                    param_type = param_info.get('type', 'string')
                    required = ' (required)' if param_info.get('required', False) else ' (optional)'
                    description = param_info.get('description', '')
                    param_desc.append(f"  - {param_name} ({param_type}){required}: {description}")
            
            params_text = '\n'.join(param_desc) if param_desc else "  No parameters required"
            
            tool_descriptions.append(
                f"### {tool.name}\n"
                f"Description: {tool.description}\n"
                f"Parameters:\n{params_text}"
            )
        
        return "\n\n".join(tool_descriptions)



    def _build_system_instructions(self) -> str:
        """Build system instructions by combining base prompt, tools, and guidelines"""
        tool_prompt = self._build_tool_prompt()
        
        # Start with base system prompt
        instructions = self.base_system_prompt
        
        # Add tools section
        instructions += f"\n\nYou have the following tools available to you:\n{tool_prompt}"
        
        # Add tool usage format
        instructions += f"""

When using tools, respond with the following JSON format:
{{
    "tool_calls": [
        {{"name": "tool_name", "arguments": {{"param1": "value1"}}}},
        {{"name": "tool_name2", "arguments": {{"param2": "value2"}}}}
    ]
}}

IMPORTANT: 
- When you give a conversational response (no tool calls), ALWAYS include <stop> at the end to indicate the conversation is complete.
- When you have completed your task and found sufficient results, include <stop> at the end of your response.
- If you're explaining that you couldn't find what the user wanted, include <stop> at the end."""
        
        # Add guidelines if provided
        if self.guidelines:
            instructions += f"\n\n{self.guidelines}"
        
        return instructions

    def run_conversation_stream(self, user_message: str = None, conversation_history: List[Dict[str, str]] = None, max_iterations: int = 40):
        """
        Run the conversation with streaming - yields messages as they are created.
        
        Args:
            user_message: New user message (required for new conversations)
            conversation_history: Existing conversation history (optional)
            max_iterations: Maximum number of iterations for tool calling
            
        Yields:
            Dict containing message info as it's created
        """
        print(f"\n🔄 Starting streaming conversation (max {max_iterations} iterations)...")
        
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
            ephemeral_text, tool_messages = process_tool_response(response, self.tools)
            
            # Store ephemeral text for access by chat route
            self.last_ephemeral_text = ephemeral_text
            
            if tool_messages:
                print(f"🛠️  Found and executed {len(tool_messages)} tool messages")
                if ephemeral_text:
                    print(f"📝 Found ephemeral text: {ephemeral_text[:100]}...")
                    # Yield ephemeral text immediately
                    yield {"type": "ephemeral", "content": ephemeral_text}
                
                messages.extend(tool_messages)
                
                if iteration == max_iterations - 1:
                    print("⚠️ Hit max iterations with tool calls pending")
                    # Add a final message explaining we hit the limit
                    final_message = {
                        "role": "assistant",
                        "content": "I apologize, but I've hit the maximum number of conversation turns. Let me summarize what I found so far..."
                    }
                    messages.append(final_message)
                    # Yield the final message
                    yield {"type": "assistant_message", "message": final_message, "all_messages": messages}
                else:
                    continue
            else:
                # Regular assistant message - add to history and yield immediately
                print("💬 No tool calls found, treating as regular assistant message")
                assistant_message = {"role": "assistant", "content": response}
                messages.append(assistant_message)
                
                # Yield the assistant message immediately
                yield {"type": "assistant_message", "message": assistant_message, "all_messages": messages}
                
                # Check if agent wants to stop
                if "<stop>" in response.lower():
                    print("🛑 Agent indicated stop with <stop> tag, ending conversation")
                    break
                else:
                    print("🔄 No <stop> tag found, agent will continue working...")
                    continue
            
        print(f"\n✅ Conversation complete with {len(messages)} total messages")
        # Final yield with complete conversation
        yield {"type": "conversation_complete", "all_messages": messages}

    def run_conversation(self, user_message: str = None, conversation_history: List[Dict[str, str]] = None, max_iterations: int = 40) -> List[Dict[str, str]]:
        """
        Run the conversation with existing history or start a new one.
        
        This method uses run_conversation_stream internally to ensure logic consistency.
        
        Args:
            user_message: New user message (required for new conversations)
            conversation_history: Existing conversation history (optional)
            max_iterations: Maximum number of iterations for tool calling
            
        Returns:
            List of all messages in the conversation
        """
        print(f"\n🔄 Starting non-streaming conversation (max {max_iterations} iterations)...")
        
        final_messages = []
        
        # Use the streaming method internally to avoid code duplication
        for stream_item in self.run_conversation_stream(user_message, conversation_history, max_iterations):
            if stream_item["type"] == "conversation_complete":
                final_messages = stream_item["all_messages"]
                break
            elif stream_item["type"] == "assistant_message":
                # Keep updating with the latest state
                final_messages = stream_item["all_messages"]
        
        print(f"\n✅ Non-streaming conversation complete with {len(final_messages)} total messages")
        return final_messages

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


def create_master_agent() -> Agent:
    """Create the master shopping agent with current tools and system prompt"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found")
        
    print("Creating master shopping agent...")
    
    # Import tools here to avoid circular imports
    from ..tools import get_tools
    
    # Create LLM
    llm = LLM(model_name="gemini-2.5-flash", api_key=GEMINI_API_KEY)
    
    # Define the base system prompt
    base_system_prompt = """You are an expert shopping assistant. You help users find products on the internet 
and display them according to their preferences and requirements.

The ui you operate in as follows:
there are two sections on the page. Left side is the chat window, right side is a display of products that get populated slowly.
When you call the display_product tool, the product will be displayed on the right side.
So you have two ways to communicate with the user. Via text on the chat window and via product cards in the right side.

You can also:
- Use get_displayed_products to see what's currently shown to the user
- Use remove_displayed_products to remove specific products by name or clear all products"""
    
    # Define the guidelines
    guidelines = """Guidelines:
1. To help users find products: use find_stores to discover relevant stores, then fetch_products to get product data
2. To display products to users: use display_product for each specific item you want to show them
3. When replying to user use conversational language and be friendly and helpful.
4. In the reply to the user dont reiterate what you have found if you showed it using display_product.
5. Make sure all products you find will match what user is looking for, we wanna avoid false positives.
6. Since you have a mechanism to display intermediate results to the user, keep searching and adding products to the right side for a while.
especially important if you havent found enough products yet.
7. If you dont find enough products from the initial search, you can always search for new stores with a variation of the query.
8. CRITICAL: When you give any conversational response (without tool calls), you MUST include <stop> at the end. This includes:
   - When you've found sufficient products and are done searching
   - When you're explaining that no suitable products were found
   - When you're asking the user a clarifying question
   - Any response that doesn't include tool calls"""
    
    # Create agent with shopping-specific configuration
    agent = Agent(
        name="Master Shopping Assistant",
        description="A helpful assistant that can find products across e-commerce stores.",
        tools=get_tools(),
        llm=llm,
        base_system_prompt=base_system_prompt,
        guidelines=guidelines
    )
    
    print(f"Master agent created with tools: {agent.get_available_tools()}")
    return agent