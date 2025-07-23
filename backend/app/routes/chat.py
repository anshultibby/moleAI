"""Chat routes using the agent system with tools"""

import json
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..modules.agent import Agent, LLM
from ..utils.tools import get_tools
from ..config import GEMINI_API_KEY
from ..utils.debug_logger import debug_log

router = APIRouter()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    conversation_id: str = None

class ChatHistory(BaseModel):
    conversation_id: str
    messages: List[Dict[str, str]]

class StreamMessage(BaseModel):
    type: str  # 'start' | 'message' | 'product' | 'complete' | 'error'
    content: Optional[str] = None
    product: Optional[Dict] = None
    error: Optional[str] = None

# Store chat histories by conversation ID
chat_histories: Dict[str, List[Dict[str, str]]] = {}

def extract_json_from_message(content: str) -> Optional[Dict]:
    """Extract JSON data from a message containing ```json blocks"""
    try:
        if "```json" in content:
            # Extract everything between ```json and ```
            json_str = content.split("```json")[1].split("```")[0].strip()
            data = json.loads(json_str)
            debug_log(f"Extracted JSON data: {json.dumps(data)[:200]}...")
            return data
    except Exception as e:
        debug_log(f"Error extracting JSON: {str(e)}")
    return None

def is_tool_call(content: str) -> bool:
    """Check if a message is a tool call"""
    try:
        if "```json" in content:
            json_data = extract_json_from_message(content)
            return json_data is not None and "tool_calls" in json_data
    except Exception as e:
        debug_log(f"Error checking tool call: {str(e)}")
    return False

def extract_products_from_tool_response(content: str) -> Optional[Dict]:
    """Extract product data from a tool response"""
    try:
        if "```json" in content:
            json_data = extract_json_from_message(content)
            if json_data and "deals_found" in json_data:
                debug_log(f"Found product data: {json.dumps(json_data)[:200]}...")
                return json_data
    except Exception as e:
        debug_log(f"Error extracting product data: {str(e)}")
    return None

def create_shopping_agent() -> Agent:
    """Create an agent instance with our tools"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found")
        
    debug_log("Creating new shopping agent...")
    
    # Create LLM
    llm = LLM(model_name="gemini-2.0-flash-exp", api_key=GEMINI_API_KEY)
    
    # Create agent with our tools
    agent = Agent(
        name="Shopping Assistant",
        description="A helpful assistant that can find products across e-commerce stores.",
        tools=get_tools(),
        llm=llm
    )
    
    debug_log(f"Agent created with tools: {agent.get_available_tools()}")
    return agent

@router.post("/chat/stream")
async def stream_chat(message: ChatMessage):
    """Stream chat responses with product search capabilities"""
    try:
        debug_log("\n" + "="*50)
        debug_log(f"New message: {message.message}")
        debug_log(f"Conversation ID: {message.conversation_id}")
        debug_log("="*50 + "\n")
        
        # Get or create chat history
        history = chat_histories.get(message.conversation_id, [])
        debug_log(f"Current history length: {len(history)}")
        
        # Create agent
        agent = create_shopping_agent()
        
        async def generate_stream():
            try:
                # Send start signal
                yield f"data: {json.dumps(StreamMessage(type='start').dict())}\n\n"
                
                # Add user message to history
                history.append({
                    "role": "user",
                    "content": message.message
                })
                
                # Run agent with full history context
                debug_log("Running conversation...")
                for msg in agent.run_conversation(message.message):
                    # Add to history
                    history.append(msg)
                    
                    if msg["role"] == "assistant":
                        debug_log(f"Processing assistant message: {msg['content'][:200]}...")
                        
                        # Skip tool calls
                        if is_tool_call(msg["content"]):
                            debug_log("Skipping tool call message")
                            continue
                            
                        # Check for product data
                        product_data = extract_products_from_tool_response(msg["content"])
                        if product_data:
                            # Stream each product
                            for product in product_data["deals_found"]:
                                debug_log(f"Streaming product: {json.dumps(product)[:200]}...")
                                stream_msg = StreamMessage(type='product', product=product)
                                yield f"data: {json.dumps(stream_msg.dict())}\n\n"
                            
                            # Stream the response message if present
                            if "response" in product_data:
                                debug_log(f"Streaming product response: {product_data['response'][:100]}...")
                                yield f"data: {json.dumps(StreamMessage(type='message', content=product_data['response']).dict())}\n\n"
                        else:
                            # If no product data, check if it's a regular message
                            if not "```json" in msg["content"]:
                                debug_log(f"Streaming regular message: {msg['content'][:100]}...")
                                yield f"data: {json.dumps(StreamMessage(type='message', content=msg['content']).dict())}\n\n"
                
                # Store updated history
                chat_histories[message.conversation_id] = history
                debug_log(f"Conversation complete. Final history length: {len(history)}")
                
                # Send completion
                yield f"data: {json.dumps(StreamMessage(type='complete').dict())}\n\n"
                
            except Exception as e:
                debug_log(f"Error in stream: {str(e)}")
                yield f"data: {json.dumps(StreamMessage(type='error', error=str(e)).dict())}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        debug_log(f"Error in route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Get chat history for a specific conversation"""
    if conversation_id not in chat_histories:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ChatHistory(
        conversation_id=conversation_id,
        messages=chat_histories[conversation_id]
    )

@router.delete("/chat/history/{conversation_id}")
async def clear_chat_history(conversation_id: str):
    """Clear chat history for a specific conversation"""
    if conversation_id in chat_histories:
        del chat_histories[conversation_id]
    return {"status": "success"}
