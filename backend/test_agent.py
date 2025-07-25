#!/usr/bin/env python3
"""
Simple test script for the Agent system
"""

from app.modules.agent import Agent, Tool, LLM


def simple_add(a: int, b: int) -> int:
    """Simple addition function"""
    return a + b


def greet(name: str) -> str:
    """Simple greeting function"""
    return f"Hello, {name}! Nice to meet you."


def search_web(query: str) -> str:
    """Mock web search function"""
    return f"Search results for '{query}': Found 3 articles about artificial intelligence, including recent advances in machine learning and neural networks."


def test_basic_functionality():
    """Test basic agent functionality without requiring API keys"""
    print("Testing basic Agent functionality...")
    
    # Create simple tools
    add_tool = Tool(
        name="add_numbers",
        description="Add two numbers together",
        function=simple_add,
        parameters={
            "a": {"type": "integer", "required": True},
            "b": {"type": "integer", "required": True}
        }
    )
    
    greet_tool = Tool(
        name="greet_person", 
        description="Greet a person by name",
        function=greet,
        parameters={
            "name": {"type": "string", "required": True}
        }
    )
    
    # Test tool creation
    print(f"✓ Created tools: {add_tool.name}, {greet_tool.name}")
    
    # Test tool execution
    result1 = add_tool.call(a=5, b=3)
    result2 = greet_tool.call(name="Alice")
    print(f"✓ Tool execution: add_numbers(5, 3) = {result1}")
    print(f"✓ Tool execution: greet_person('Alice') = {result2}")
    
    # Create a mock LLM for testing (doesn't need API key)
    class MockLLM(LLM):
        def __init__(self):
            self.model_name = "mock"
            self.client_type = "mock"
        
        def chat_completion(self, messages):
            # Return a mock tool call for testing
            return '''{"tool_call": {"name": "add_numbers", "arguments": {"a": 10, "b": 20}}}'''
    
    # Create agent with mock LLM
    mock_llm = MockLLM()
    agent = Agent(
        name="TestAgent",
        description="A test agent for basic functionality",
        tools=[add_tool, greet_tool],
        llm=mock_llm
    )
    
    print(f"✓ Created agent: {agent.name}")
    print(f"✓ Agent has {len(agent.tools)} tools")
    
    # Test system instructions generation
    instructions = agent.system_instructions
    assert "add_numbers" in instructions
    assert "greet_person" in instructions
    print("✓ System instructions generated correctly")
    
    # Test conversation with tool call
    messages = agent.run_conversation("Add 5 and 7")
    assert len(messages) >= 3  # system, user, assistant (and possibly function)
    print("✓ Conversation with tool call working")
    
    print("\n🎉 All basic functionality tests passed!")


def test_with_real_llm():
    """Test with real LLM if API key is available"""
    from app.config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        print("\n⚠️  GEMINI_API_KEY not found - skipping real LLM test")
        print("   Set GEMINI_API_KEY environment variable to test with real LLM")
        return
    
    print("\n" + "="*50)
    print("Testing with real Gemini LLM...")
    print("="*50)
    
    # Create tools
    add_tool = Tool(
        name="add_numbers",
        description="Add two numbers together", 
        function=simple_add,
        parameters={
            "a": {"type": "integer", "required": True},
            "b": {"type": "integer", "required": True}
        }
    )
    
    greet_tool = Tool(
        name="greet_person",
        description="Greet a person by name",
        function=greet,
        parameters={
            "name": {"type": "string", "required": True}
        }
    )
    
    search_tool = Tool(
        name="search_web",
        description="Search the web for information",
        function=search_web,
        parameters={
            "query": {"type": "string", "required": True}
        }
    )
    
    # Create real LLM
    llm = LLM(model_name="gemini-2.0-flash-exp", api_key=GEMINI_API_KEY)
    
    # Create agent
    agent = Agent(
        name="MathHelper",
        description="A helpful assistant that can do basic math, greetings, and web searches",
        tools=[add_tool, greet_tool, search_tool],
        llm=llm
    )
    
    # Test a simple math conversation
    print("Running conversation: 'Add 15 and 25'")
    messages = agent.run_conversation("Add 15 and 25")
    
    print("\nConversation flow:")
    for msg in messages:
        print(f"{msg['role'].upper()}: {msg['content']}")
    
    # Test web search conversation
    print("\n" + "-"*30)
    print("Running conversation: 'Search for information about artificial intelligence'")
    messages2 = agent.run_conversation("Search for information about artificial intelligence")
    
    print("\nConversation flow:")
    for msg in messages2:
        print(f"{msg['role'].upper()}: {msg['content']}")
    
    print("\n🎉 Real LLM test completed!")


if __name__ == "__main__":
    # Run tests
    test_basic_functionality()
    test_with_real_llm() 