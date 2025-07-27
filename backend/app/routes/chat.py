"""Chat routes using the agent system with tools"""

import json
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..modules.agent import Agent, LLM, create_master_agent
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
    type: str  # 'start' | 'message' | 'ephemeral' | 'product' | 'complete' | 'error'
    content: Optional[str] = None
    product: Optional[Dict] = None
    error: Optional[str] = None

# Store chat histories by conversation ID
chat_histories: Dict[str, List[Dict[str, str]]] = {}

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
        
        # Create master agent
        agent = create_master_agent()
        
        async def generate_stream():
            try:
                # Only reset product emitter for brand new conversations (no existing history)
                if not existing_history:
                    debug_log("New conversation detected - resetting product emitter")
                    get_product_emitter().reset_conversation()
                
                # Send start signal
                yield f"data: {json.dumps(StreamMessage(type='start').dict())}\n\n"
                
                # Run agent with streaming
                if existing_history:
                    # Continue existing conversation
                    debug_log("Continuing existing conversation with history...")
                    conversation_stream = agent.run_conversation_stream(
                        user_message=message.message,
                        conversation_history=existing_history
                    )
                else:
                    # Start new conversation
                    debug_log("Starting new conversation...")
                    conversation_stream = agent.run_conversation_stream(user_message=message.message)
                
                final_messages = None
                
                # Process streaming results
                for stream_item in conversation_stream:
                    debug_log(f"Processing stream item: {stream_item['type']}")
                    
                    if stream_item["type"] == "ephemeral":
                        # Stream ephemeral text immediately
                        debug_log(f"Streaming ephemeral text: {stream_item['content'][:100]}...")
                        yield f"data: {json.dumps(StreamMessage(type='ephemeral', content=stream_item['content']).dict())}\n\n"
                    
                    elif stream_item["type"] == "assistant_message":
                        # Stream assistant message immediately
                        msg = stream_item["message"]
                        debug_log(f"Streaming assistant message: {msg['content'][:100]}...")
                        yield f"data: {json.dumps(StreamMessage(type='message', content=msg['content']).dict())}\n\n"
                        
                        # Update final messages for storage
                        final_messages = stream_item["all_messages"]
                    
                    elif stream_item["type"] == "conversation_complete":
                        # Store final conversation state
                        final_messages = stream_item["all_messages"]
                    
                    # Check for new products from the event emitter after each stream item
                    new_products = get_product_emitter().get_new_products()
                    for product in new_products:
                        debug_log(f"Streaming product from event: {product.get('product_name', 'Unknown')}")
                        stream_msg = StreamMessage(type='product', product=product)
                        yield f"data: {json.dumps(stream_msg.dict())}\n\n"
                
                # Store updated conversation history
                if final_messages:
                    chat_histories[message.conversation_id] = final_messages
                    debug_log(f"Conversation complete. Final history length: {len(final_messages)}")
                
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
