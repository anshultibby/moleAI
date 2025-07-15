from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..models.chat import ChatMessage, ChatResponse
from ..utils.shopping_pipeline import process_shopping_query_with_tools, preprocess_shopping_query
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()

# Get API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Simple in-memory storage for demo (replace with proper database later)
chat_history = []

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
        
        print(f"Processing query: {message.message}")  # Debug logging
        
        # Process with Gemini AI using tool calling architecture
        deals_found, conversation_messages = await process_shopping_query_with_tools_async(
            message.message, 
            GEMINI_API_KEY
        )
        
        print(f"Deals found: {len(deals_found)}")  # Debug logging
        print(f"Conversation messages: {len(conversation_messages)}")  # Debug logging
        
        # Generate final response based on the conversation
        if deals_found:
            # Check if deals_found contains raw content (new format) or structured data (old format)
            first_deal = deals_found[0] if deals_found else {}
            
            if 'markdown' in first_deal:
                # New format: raw content from Zara
                # Extract the assistant's analysis from conversation messages
                assistant_messages = [msg for msg in conversation_messages if msg.get('role') == 'assistant']
                if assistant_messages:
                    # Get the last assistant message which should contain the analysis
                    ai_response = assistant_messages[-1].get('content', 'I found some products but couldn\'t analyze them properly.')
                else:
                    ai_response = f"I found search results from Zara, but couldn't process them properly. Here's what I found:\n\n"
                    for i, deal in enumerate(deals_found, 1):
                        ai_response += f"{i}. Search results from {deal.get('source', 'Zara')}\n"
                        ai_response += f"   URL: {deal.get('url', 'N/A')}\n"
                        ai_response += f"   Content length: {len(deal.get('markdown', ''))} characters\n\n"
            else:
                # Old format: structured product data
                ai_response = f"I found {len(deals_found)} deals for you! Here's what I discovered:\n\n"
                for i, deal in enumerate(deals_found, 1):
                    product_name = deal.get('product_name', 'Unknown product')
                    price = deal.get('price', 'Unknown price')
                    store = deal.get('store', 'Unknown store')
                    rating = deal.get('rating', 'N/A')
                    availability = deal.get('availability', 'Unknown')
                    url = deal.get('url', '')
                    
                    ai_response += f"{i}. **{product_name}** - {price} at {store}\n"
                    if rating != 'N/A':
                        ai_response += f"   Rating: {rating}\n"
                    if availability != 'Unknown':
                        ai_response += f"   Availability: {availability}\n"
                    if url:
                        ai_response += f"   Link: {url}\n"
                    ai_response += "\n"
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
    # In a real implementation, you might want to run this in a thread pool
    # to avoid blocking the async event loop
    try:
        deals_found, messages = process_shopping_query_with_tools(query, api_key)
        return deals_found, messages
    except Exception as e:
        # Return empty results on error
        return [], [{"role": "assistant", "content": f"Error processing query: {str(e)}"}] 