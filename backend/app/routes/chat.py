"""Chat routes using the agent system with tools"""

import json
from typing import Dict, List
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
        
        # Get or create chat history
        history = chat_histories.get(message.conversation_id, [])
        debug_log(f"Current history length: {len(history)}")
        
        # Create agent
        agent = create_shopping_agent()
        
        async def generate_stream():
            try:
                # Send start signal
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                
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
                    
                    # Only stream assistant messages that aren't tool calls
                    if msg["role"] == "assistant" and "```json" not in msg["content"]:
                        debug_log(f"Streaming message: {msg['content'][:100]}...")
                        yield f"data: {json.dumps({'type': 'message', 'content': msg['content']})}\n\n"
                
                # Store updated history
                chat_histories[message.conversation_id] = history
                debug_log(f"Conversation complete. Final history length: {len(history)}")
                
                # Send completion
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                
            except Exception as e:
                debug_log(f"Error in stream: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
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
