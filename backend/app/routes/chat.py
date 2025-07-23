import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..models.chat import ChatMessage
from ..utils.streaming_pipeline import process_shopping_query_streaming
from ..utils.streaming_service import get_streaming_service
from ..config import GEMINI_API_KEY
router = APIRouter()

# Simple in-memory storage for demo (replace with proper database later)
chat_history = []

@router.post("/chat/stream")
async def stream_chat(message: ChatMessage):
    """
    Stream chat updates in real-time as they happen
    """
    import time
    entry_time = time.time()
    print(f"🚀 ENTRY: stream_chat called with message: {message.message}")
    
    async def generate_stream():
        generator_start = time.time()
        print(f"🚀 GENERATOR: Starting generate_stream function at {time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"🚀 GENERATOR: Time since entry: {generator_start - entry_time:.3f}s")
        
        try:
            print(f"🚀 IMPORT: About to import streaming_service")
            
            # Clear any previous streaming state before starting new query
            import_start = time.time()
            streaming_service = get_streaming_service()
            import_end = time.time()
            print(f"🚀 SERVICE: Got streaming service in {import_end - import_start:.3f}s")
            
            clear_start = time.time()
            streaming_service.clear_queue()
            clear_end = time.time()
            print(f"🚀 SERVICE: Cleared queue in {clear_end - clear_start:.3f}s")
            
            # Send immediate start signal to confirm connection
            yield_start = time.time()
            yield f"data: {json.dumps({'type': 'start', 'message': 'Connection established'})}\n\n"
            yield_end = time.time()
            print(f"🚀 YIELDED: Start signal sent in {yield_end - yield_start:.3f}s")
            
            # Process query with streaming callbacks
            pipeline_start = time.time()
            print(f"🚀 PIPELINE: About to call process_shopping_query_with_tools_streaming at {time.strftime('%H:%M:%S.%f')[:-3]}")
            
            async for update in process_shopping_query_with_tools_streaming(message.message, GEMINI_API_KEY):
                update_time = time.time()
                print(f"🚀 STREAM: Got update: {update.get('type', 'unknown')} at {time.strftime('%H:%M:%S.%f')[:-3]}")
                yield f"data: {json.dumps(update)}\n\n"
            
            # Send completion
            complete_start = time.time()
            print(f"🚀 COMPLETE: Sending completion message")
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except Exception as e:
            print(f"🚀 ERROR: Exception in generate_stream: {e}")
            import traceback
            print(f"🚀 ERROR: Traceback: {traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    response_start = time.time()
    print(f"🚀 RETURN: Returning StreamingResponse at {time.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"🚀 RETURN: Time since entry: {response_start - entry_time:.3f}s")
    
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


@router.get("/chat/history")
async def get_chat_history():
    """
    Get chat history
    """
    return {"messages": chat_history}


async def process_shopping_query_with_tools_streaming(query: str, api_key: str):
    """
    Stream shopping query processing with real-time updates using the new agentic system
    """
    import time
    wrapper_start = time.time()
    print(f"🚀 WRAPPER: process_shopping_query_with_tools_streaming called with query: {query}")
    print(f"🚀 WRAPPER: Started at {time.strftime('%H:%M:%S.%f')[:-3]}")
    
    try:
        # Import the new streaming agent
        from ..modules.streaming_agent import process_query_with_streaming_agent
        
        print(f"🚀 WRAPPER: Using new streaming agent for query: {query}")
        
        # Use the new streaming agent system
        async for update in process_query_with_streaming_agent(query):
            update_time = time.time()
            print(f"🚀 AGENT: Got update: {update.get('type', 'unknown')} at {time.strftime('%H:%M:%S.%f')[:-3]}")
            yield update
                
    except Exception as e:
        print(f"🚀 WRAPPER: Exception in wrapper: {e}")
        import traceback
        print(f"🚀 WRAPPER: Traceback: {traceback.format_exc()}")
        
        # Fallback to original pipeline if agent fails
        try:
            print(f"🚀 FALLBACK: Falling back to original pipeline")
            async for update in process_shopping_query_streaming(query, api_key):
                print(f"🚀 FALLBACK: Got update: {update.get('type', 'unknown')}")
                yield update
        except Exception as fallback_e:
            print(f"🚀 FALLBACK: Fallback also failed: {fallback_e}")
            yield {"type": "error", "message": f"Both agent and fallback failed: {str(e)} | {str(fallback_e)}"}
