"""Chat routes using the agent system with tools"""

import json
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..modules.agent import Agent, LLM
from ..tools import get_tools
from ..config import GEMINI_API_KEY
from ..utils.debug_logger import debug_log
from ..utils.product_event_emitter import get_product_emitter

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
        
        # Get existing chat history or start with system message
        existing_history = chat_histories.get(message.conversation_id, [])
        debug_log(f"Existing history length: {len(existing_history)}")
        
        # Create agent
        agent = create_shopping_agent()
        
        async def generate_stream():
            try:
                # Only reset product emitter for brand new conversations (no existing history)
                if not existing_history:
                    debug_log("New conversation detected - resetting product emitter")
                    get_product_emitter().reset_conversation()
                
                # Send start signal
                yield f"data: {json.dumps(StreamMessage(type='start').dict())}\n\n"
                
                # Run agent with conversation history and new message
                if existing_history:
                    # Continue existing conversation
                    debug_log("Continuing existing conversation with history...")
                    updated_messages = agent.run_conversation(
                        user_message=message.message,
                        conversation_history=existing_history
                    )
                else:
                    # Start new conversation
                    debug_log("Starting new conversation...")
                    updated_messages = agent.run_conversation(user_message=message.message)
                
                # Process new messages (everything after the existing history)
                start_index = len(existing_history)
                new_messages = updated_messages[start_index:]
                debug_log(f"Processing {len(new_messages)} new messages...")
                
                for msg in new_messages:
                    debug_log(f"Processing message: {msg['role']} - {msg['content'][:100]}...")
                    
                    if msg["role"] == "assistant":
                        # Stream assistant messages directly to user
                        debug_log(f"Streaming assistant message: {msg['content'][:100]}...")
                        yield f"data: {json.dumps(StreamMessage(type='message', content=msg['content']).dict())}\n\n"
                    
                    # Check for new products from the event emitter after each message
                    new_products = get_product_emitter().get_new_products()
                    for product in new_products:
                        debug_log(f"Streaming product from event: {product.get('product_name', 'Unknown')}")
                        stream_msg = StreamMessage(type='product', product=product)
                        yield f"data: {json.dumps(stream_msg.dict())}\n\n"
                    
                    # Note: We don't stream 'tool' or 'system' or 'user' messages to the frontend
                    # These are internal conversation management messages
                
                # Store updated conversation history
                chat_histories[message.conversation_id] = updated_messages
                debug_log(f"Conversation complete. Final history length: {len(updated_messages)}")
                
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
