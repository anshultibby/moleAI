"""
Example usage of the Agent system with OpenAI Swarm-style agentic loop
"""
from agent import Agent, Tool, LLM
from config import GEMINI_API_KEY

def get_weather(location: str) -> str:
    """Mock weather function"""
    return f"The weather in {location} is sunny, 72°F"


def calculate(expression: str) -> str:
    """Safe calculator function"""
    try:
        # Simple eval for demo - in production use a proper expression parser
        allowed_chars = set('0123456789+-*/.() ')
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"{expression} = {result}"
        else:
            return "Error: Invalid characters in expression"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


def search_web(query: str) -> str:
    """Mock web search function"""
    return f"Search results for '{query}': Found 10 relevant articles about {query}"


def create_example_agent():
    """Create an example agent with some tools"""
    
    # Create tools
    weather_tool = Tool(
        name="get_weather",
        description="Get current weather for a location",
        function=get_weather,
        parameters={
            "location": {
                "type": "string",
                "description": "The city or location to get weather for",
                "required": True
            }
        }
    )
    
    calculator_tool = Tool(
        name="calculate",
        description="Perform mathematical calculations",
        function=calculate,
        parameters={
            "expression": {
                "type": "string", 
                "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')",
                "required": True
            }
        }
    )
    
    search_tool = Tool(
        name="search_web",
        description="Search the web for information",
        function=search_web,
        parameters={
            "query": {
                "type": "string",
                "description": "Search query",
                "required": True
            }
        }
    )
    
    # Create LLM using centralized config
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")
    
    print(f"✓ Using Gemini API key: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
    
    llm = LLM(
        model_name="gemini-2.0-flash-exp",
        api_key=GEMINI_API_KEY
    )
    
    # Create agent
    agent = Agent(
        name="Assistant",
        description="A helpful assistant that can get weather, do calculations, and search the web",
        tools=[weather_tool, calculator_tool, search_tool],
        llm=llm
    )
    
    return agent


def demo_conversation():
    """Demo the agentic conversation loop"""
    agent = create_example_agent()
    
    # Example conversations
    test_queries = [
        "What's the weather like in San Francisco?",
        "Calculate 15 * 23 + 7",
        "Search for information about artificial intelligence",
        "What's the weather in Tokyo and what's 100 + 200?",  # Multi-step
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"USER: {query}")
        print(f"{'='*50}")
        
        # Run the conversation
        conversation = agent.run_conversation(query)
        
        # Print the conversation flow
        for i, msg in enumerate(conversation):
            if msg['type'] == 'message':
                print(f"{msg['role'].upper()}: {msg['content']}")
            elif msg['type'] == 'tool_call':
                tool_call = msg['tool_call']
                print(f"TOOL_CALL: {tool_call['name']}({tool_call['arguments']})")
            elif msg['type'] == 'tool_result':
                print(f"TOOL_RESULT: {msg['content']}")
        
        print("\n" + "-"*30)


if __name__ == "__main__":
    # Run the demo
    demo_conversation() 