from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from ..models.chat import ChatMessage, ChatResponse
from ..utils.shopping_pipeline import process_shopping_query_with_tools, preprocess_shopping_query
from ..utils.streaming_pipeline import process_shopping_query_streaming
from ..utils.shopping_pipeline_v2 import process_shopping_query_simple
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
            # Check API keys
            if not GEMINI_API_KEY:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Gemini API key not configured'})}\n\n"
                return
            
            # Clear any previous streaming state before starting new query
            from ..utils.streaming_service import get_streaming_service
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

@router.post("/chat", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """
    Process a chat message and return AI response for shopping deals using Gemini with tool calling
    """
    try:
        # Debug: Check API key values
        print(f"GEMINI_API_KEY: {'***' + GEMINI_API_KEY[-10:] if GEMINI_API_KEY else 'None'}")
        print(f"FIRECRAWL_API_KEY: {'***' + FIRECRAWL_API_KEY[-10:] if FIRECRAWL_API_KEY else 'None'}")
        
        # Check if API keys are configured
        if not GEMINI_API_KEY:
            print("GEMINI_API_KEY is missing or empty")
            raise HTTPException(
                status_code=500, 
                detail="Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
            )
        
        if not FIRECRAWL_API_KEY:
            print("FIRECRAWL_API_KEY is missing or empty")
            raise HTTPException(
                status_code=500, 
                detail="Firecrawl API key not configured. Please set FIRECRAWL_API_KEY environment variable."
            )
        
        # Add timestamp if not provided
        if not message.timestamp:
            message.timestamp = datetime.now()
        
        # Store user message
        chat_history.append({
            "role": "user",
            "content": message.message,
            "timestamp": message.timestamp.isoformat()
        })
        
        print(f"Processing query: {message.message}")
        
        # Process with Gemini AI using tool calling architecture
        deals_found, conversation_messages, ai_response = await process_shopping_query_with_tools_async(
            message.message, 
            GEMINI_API_KEY
        )
        
        print(f"Deals found: {len(deals_found)}")  # Debug logging
        print(f"Conversation messages: {len(conversation_messages)}")  # Debug logging
        print(f"AI Response: {ai_response}")  # Debug logging
        
        # Use the AI response from the shopping pipeline (no need to generate it here)
        # The deals_found will be sent separately to the frontend for the product panel
        
        # Store AI response
        response_time = datetime.now()
        chat_history.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": response_time.isoformat()
        })
        
        return ChatResponse(
            response=ai_response,
            timestamp=response_time,
            deals_found=deals_found
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")  # Debug logging
        print(f"Error type: {type(e)}")  # Debug logging
        import traceback
        print(f"Traceback: {traceback.format_exc()}")  # Debug logging
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/chat/simple")
async def simple_chat(message: ChatMessage):
    """
    Simple chat using standard OpenAI conversation history pattern
    """
    async def generate_stream():
        try:
            # Check API keys
            if not OPENAI_API_KEY:
                yield f"data: {json.dumps({'type': 'error', 'message': 'OpenAI API key not configured'})}\n\n"
                return
            
            # DON'T send start message - users want products not progress  
            # yield f"data: {json.dumps({'type': 'start', 'message': 'Starting search...'})}\n\n"
            
            # Process query with the new simplified pipeline
            for update in process_shopping_query_simple(message.message, OPENAI_API_KEY):
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
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    ) 