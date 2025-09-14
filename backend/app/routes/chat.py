"""Chat routes for the shopping deals agent"""

import ast
import asyncio
import json
import traceback
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from enum import Enum

from app.modules.agent import Agent
from app.models import (
    Message, 
    UserMessage,
    SystemMessage, 
    AssistantMessage,
    ChatCompletionResponse,
    StreamEventType
)
from app.config import OPENAI_API_KEY, XLM_API_KEY
from app.prompts import BASIC_ASSISTANT_PROMPT
from app.utils.chat_storage import chat_storage
from app.llm.router import LLMRouter
# Import tool definitions to register them
import app.tools.definitions

router = APIRouter()

# Available LLM models enum
class AvailableModels(str, Enum):
    """Enum of available LLM models"""
    # XLM (Z.AI) models
    GLM_4_5V = "glm-4.5v"
    
    # OpenAI models  
    GPT_5 = "gpt-5"

# Simple request model for the API endpoint
class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None
    model: AvailableModels = AvailableModels.GLM_4_5V  # Default to XLM model

# Initialize global LLM router
llm_router = LLMRouter(xlm_api_key=XLM_API_KEY)

# Store agents by conversation ID
agents: Dict[str, Agent] = {}

def get_or_create_agent(conversation_id: str, stream_callback=None, model: AvailableModels = AvailableModels.GLM_4_5V) -> Agent:
    """Get existing agent or create new one for conversation"""
    if conversation_id not in agents:
        agents[conversation_id] = Agent(
            system_prompt=BASIC_ASSISTANT_PROMPT,
            model=model.value,  # Convert enum to string value
            reasoning_effort="low",
            llm_router=llm_router,
            stream_callback=stream_callback,
            conversation_id=conversation_id
        )
    else:
        # Update existing agent's stream callback
        agents[conversation_id].stream_callback = stream_callback
    
    return agents[conversation_id]

def end_conversation_tracking(conversation_id: str, user_message: str, agent: Agent, end_reason: str = "completed") -> None:
    """Helper method to mark conversation as ended"""
    try:
        conversation_id_to_save = conversation_id or "default"
        
        # Create final metadata about the conversation
        metadata = {
            "final_user_message": user_message,
            "model": agent.model,
            "reasoning_effort": agent.reasoning_effort,
            "total_messages": len(agent.get_message_history()),
            "end_reason": end_reason
        }
        
        # Get resources from agent context if available
        resources = None
        if hasattr(agent, 'context_vars') and agent.context_vars:
            resources = agent.context_vars.get('resources')
        
        # Mark conversation as ended
        chat_storage.end_conversation(
            conversation_id=conversation_id_to_save,
            metadata=metadata,
            end_reason=end_reason,
            resources=resources
        )
        print(f"Ended conversation tracking: {conversation_id_to_save} (reason: {end_reason})")
        
    except Exception as e:
        print(f"Error ending conversation tracking: {e}")
        # Don't fail the request if ending fails



def format_chat_history_for_api(history: List[Any]) -> List[Dict[str, Any]]:
    """Helper to format chat history for API response"""
    messages = []
    for msg in history:
        if hasattr(msg, 'role') and hasattr(msg, 'content'):
            messages.append({
                "role": msg.role,
                "content": str(msg.content)
            })
    return messages

@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat responses using the agent system"""
    try:
        print(f"New message: {request.message}")
        print(f"Conversation ID: {request.conversation_id}")
        
        async def generate_stream():
            agent = None
            try:
                # Get or create agent
                agent = get_or_create_agent(request.conversation_id or "default", None, request.model)
                
                # Send start signal
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                
                # Create user message
                user_message = UserMessage(content=request.message)
                
                # Run the agent conversation and stream events in real-time
                final_response = None
                async for event in agent.run(user_message):
                    if event.type == StreamEventType.COMPLETE:
                        final_response = event.response
                        break
                    else:
                        # Convert pydantic model to dict for JSON serialization
                        event_dict = event.model_dump()
                        yield f"data: {json.dumps(event_dict)}\n\n"
                
                # End conversation tracking
                end_conversation_tracking(request.conversation_id, request.message, agent, "completed")
                
                # Send completion
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                
            except Exception as e:
                print(f"Error in stream: {str(e)}")
                traceback.print_exc()
                # End conversation tracking with error reason if agent was created
                if agent:
                    try:
                        end_conversation_tracking(request.conversation_id, request.message, agent, "error")
                    except:
                        pass  # Don't fail if ending fails
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
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
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Get chat history for a specific conversation"""
    if conversation_id not in agents:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    agent = agents[conversation_id]
    history = agent.get_message_history()
    messages = format_chat_history_for_api(history)
    
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

@router.get("/chat/history/list")
async def list_chat_histories():
    """List all available chat histories"""
    try:
        conversations = chat_storage.list_conversations()
        return {
            "status": "success",
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing chat histories: {str(e)}")

@router.get("/chat/history/file/{conversation_id}")
async def get_saved_chat_history(conversation_id: str, timestamp: str = None):
    """Get saved chat history from file storage"""
    try:
        history_data = chat_storage.load_chat_history(conversation_id, timestamp)
        if history_data is None:
            raise HTTPException(status_code=404, detail="Chat history not found")
        
        return {
            "status": "success",
            "data": history_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading chat history: {str(e)}")

@router.delete("/chat/history/cleanup")
async def cleanup_old_chat_histories(days_to_keep: int = 30):
    """Clean up old chat history files"""
    try:
        deleted_count = chat_storage.cleanup_old_files(days_to_keep)
        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} old chat history files",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")


@router.get("/models")
async def list_models():
    """List available LLM models and their providers"""
    try:
        supported_models = llm_router.get_supported_models()
        default_model = llm_router.get_default_model()
        
        return {
            "available_models": [model.value for model in AvailableModels],
            "supported_models": supported_models,
            "default_model": default_model,
            "model_descriptions": {
                AvailableModels.GLM_4_5V.value: "GLM-4.5V - XLM Vision Model (Z.AI) - Supports multimodal content",
            }
        }
    except Exception as e:
        print(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))