"""Chat routes for the shopping deals agent"""

import json
import asyncio
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.modules.agent import Agent
from app.models import (
    Message, ThinkingResponse, ToolCallsResponse, AssistantResponse, 
    OpenAIResponse, ResponseOutputMessage
)
from app.config import OPENAI_API_KEY
from app.prompts import BASIC_ASSISTANT_PROMPT
# Import tool definitions to register them
import app.tools.definitions

router = APIRouter()

# Simple request model for the API endpoint
class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

# Store agents by conversation ID
agents: Dict[str, Agent] = {}

def get_or_create_agent(conversation_id: str) -> Agent:
    """Get existing agent or create new one for conversation"""
    if conversation_id not in agents:
        agents[conversation_id] = Agent(
            system_prompt=BASIC_ASSISTANT_PROMPT,
            model="gpt-5",
            reasoning_effort="medium",
            api_key=OPENAI_API_KEY
        )
    
    return agents[conversation_id]

@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat responses using the agent system"""
    try:
        print(f"New message: {request.message}")
        print(f"Conversation ID: {request.conversation_id}")
        
        # Get or create agent for this conversation
        agent = get_or_create_agent(request.conversation_id or "default")
        
        async def generate_stream():
            try:
                # Send start signal
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                
                # Create user message
                user_message = Message(role="user", content=request.message)
                
                # Run the agent conversation
                conversation = agent.run(user_message)
                
                try:
                    while True:
                        result = next(conversation)
                        
                        if isinstance(result, ThinkingResponse):
                            # Stream thinking content as ephemeral messages for the thinking panel
                            if result.content:
                                for content_item in result.content:
                                    stream_data = {
                                        'type': 'ephemeral',
                                        'content': content_item
                                    }
                                    yield f"data: {json.dumps(stream_data)}\n\n"
                            
                            # Also stream summary if available
                            if result.summary:
                                for summary_item in result.summary:
                                    stream_data = {
                                        'type': 'ephemeral',
                                        'content': f"Summary: {summary_item}"
                                    }
                                    yield f"data: {json.dumps(stream_data)}\n\n"
                            
                        elif isinstance(result, ToolCallsResponse):
                            # This shouldn't happen as the agent handles tool calls internally
                            # and continues the conversation automatically
                            pass
                            
                        elif isinstance(result, AssistantResponse):
                            # Stream the assistant response using typed models
                            response_text = ""
                            
                            # Extract text from typed response
                            if isinstance(result.response, OpenAIResponse):
                                for output_item in result.response.output:
                                    if isinstance(output_item, ResponseOutputMessage):
                                        for content_item in output_item.content:
                                            response_text += content_item.text
                            else:
                                # Fallback for untyped response
                                if hasattr(result.response, 'output_text'):
                                    response_text = result.response.output_text
                                elif hasattr(result.response, 'output') and result.response.output:
                                    for item in result.response.output:
                                        if hasattr(item, 'type') and item.type == "message":
                                            if hasattr(item, 'content') and item.content:
                                                for content_item in item.content:
                                                    if hasattr(content_item, 'text'):
                                                        response_text += content_item.text
                                                    elif isinstance(content_item, str):
                                                        response_text += content_item
                            
                            message_data = {
                                'type': 'message',
                                'content': response_text
                            }
                            yield f"data: {json.dumps(message_data)}\n\n"
                            
                            # End the conversation since we don't expect user input in streaming
                            conversation.send(None)
                            break
                            
                except StopIteration:
                    # Conversation ended normally
                    pass
                
                # Send completion
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                
            except Exception as e:
                print(f"Error in stream: {str(e)}")
                import traceback
                traceback.print_exc()
                error_data = {'type': 'error', 'error': str(e)}
                yield f"data: {json.dumps(error_data)}\n\n"
        
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
        print(f"Error in route: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Get chat history for a specific conversation"""
    if conversation_id not in agents:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    agent = agents[conversation_id]
    history = agent.get_message_history()
    
    # Convert to simple format for API response
    messages = []
    for msg in history:
        if hasattr(msg, 'role') and hasattr(msg, 'content'):
            messages.append({
                "role": msg.role,
                "content": str(msg.content)
            })
    
    return {
        "conversation_id": conversation_id,
        "messages": messages
    }

@router.delete("/chat/history/{conversation_id}")
async def clear_chat_history(conversation_id: str):
    """Clear chat history for a specific conversation"""
    if conversation_id in agents:
        del agents[conversation_id]
    return {"status": "success"}

@router.get("/chat/test")
async def test_chat():
    """Simple test endpoint"""
    return {"message": "Chat API is working with GPT-5!"}