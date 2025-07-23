from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from ..models.chat import ChatMessage, ChatResponse
from ..utils.shopping_pipeline import process_shopping_query_with_tools, preprocess_shopping_query
from ..utils.streaming_pipeline import process_shopping_query_streaming
from ..utils.shopping_pipeline_v2 import process_shopping_query_simple
from ..utils.streaming_service import get_streaming_service

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()

# Get API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Simple in-memory storage for demo (replace with proper database later)
chat_history = []

@router.post("/chat/stream")
async def stream_chat(message: ChatMessage):
    """
    Stream chat updates in real-time as they happen
    """
    async def generate_stream():
        try:
            
            # Clear any previous streaming state before starting new query
            streaming_service = get_streaming_service()
            streaming_service.clear_queue()
            
            # DON'T send start message - users want products not progress
            # yield f"data: {json.dumps({'type': 'start', 'message': 'Starting search...'})}\n\n"
            
            # Process query with streaming callbacks
            async for update in process_shopping_query_with_tools_streaming(message.message, GEMINI_API_KEY):
                yield f"data: {json.dumps(update)}\n\n"
            
            # Send completion
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.get("/chat/history")
async def get_chat_history():
    """
    Get chat history
    """
    return {"messages": chat_history}

async def process_shopping_query_with_tools_async(query: str, api_key: str) -> tuple:
    """
    Async wrapper for the shopping query processing with tools
    """
    try:
        # Import the async version of the shopping pipeline
        from ..utils.shopping_pipeline import process_shopping_query_with_tools_async as pipeline_async
        deals_found, messages, final_chat_response = await pipeline_async(query, api_key)
        return deals_found, messages, final_chat_response
    except Exception as e:
        # Return empty results on error
        return [], [{"role": "assistant", "content": f"Error processing query: {str(e)}"}], f"Sorry, I encountered an error: {str(e)}"

async def process_shopping_query_with_tools_streaming(query: str, api_key: str):
    """
    Stream shopping query processing with real-time updates using the new clean pipeline
    """
    try:
        # Use the new clean streaming pipeline
        async for update in process_shopping_query_streaming(query, api_key):
            yield update
                
    except Exception as e:
        yield {"type": "error", "message": str(e)}

# Removed simple_chat endpoint - OpenAI pipeline no longer needed 