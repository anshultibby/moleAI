from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..models.chat import ChatMessage, ChatResponse
from ..utils.shopping_pipeline import process_shopping_query_with_tools, preprocess_shopping_query
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Simple in-memory storage for demo (replace with proper database later)
chat_history = []

@router.post("/chat", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """
    Process a chat message and return AI response for shopping deals using Gemini with tool calling
    """
    try:
        # Check if API key is configured
        if not GEMINI_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
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
        
        # Process with Gemini AI using tool calling architecture
        deals_found, conversation_messages = await process_shopping_query_with_tools_async(
            message.message, 
            GEMINI_API_KEY
        )
        
        # Generate final response based on the conversation
        if deals_found:
            ai_response = f"I found {len(deals_found)} deals for you! Here's what I discovered:\n\n"
            for i, deal in enumerate(deals_found, 1):
                product_name = deal.get('product_name', 'Unknown product')
                price = deal.get('price', 'Unknown price')
                store = deal.get('store', 'Unknown store')
                ai_response += f"{i}. {product_name} - {price} at {store}\n"
        else:
            # Extract the last assistant message from conversation
            assistant_messages = [msg for msg in conversation_messages if msg.get('role') == 'assistant']
            if assistant_messages:
                ai_response = assistant_messages[-1].get('content', 'I searched for deals but didn\'t find specific results.')
            else:
                ai_response = "I searched for deals but didn't find specific results."
        
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
    # In a real implementation, you might want to run this in a thread pool
    # to avoid blocking the async event loop
    try:
        deals_found, messages = process_shopping_query_with_tools(query, api_key)
        return deals_found, messages
    except Exception as e:
        # Return empty results on error
        return [], [{"role": "assistant", "content": f"Error processing query: {str(e)}"}] 