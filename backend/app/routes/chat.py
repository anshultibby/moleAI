"""Chat routes for the shopping deals agent"""

import json
from typing import Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.modules.agent import Agent
from app.models import (
    Message, ThinkingResponse, ToolCallsResponse, AssistantResponse, ToolExecutionResponse,
    OpenAIResponse, ResponseOutputMessage, StreamStartMessage, StreamMessageContent,
    StreamProductMessage, StreamProductGridMessage, StreamEphemeralMessage,
    StreamToolExecutionMessage, StreamCompleteMessage, StreamErrorMessage
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

def get_or_create_agent(conversation_id: str, stream_callback=None) -> Agent:
    """Get existing agent or create new one for conversation"""
    if conversation_id not in agents:
        agents[conversation_id] = Agent(
            system_prompt=BASIC_ASSISTANT_PROMPT,
            model="gpt-5",
            reasoning_effort="low",
            api_key=OPENAI_API_KEY,
            stream_callback=stream_callback
        )
    else:
        # Update existing agent's stream callback
        agents[conversation_id].stream_callback = stream_callback
    
    return agents[conversation_id]

@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat responses using the agent system"""
    try:
        print(f"New message: {request.message}")
        print(f"Conversation ID: {request.conversation_id}")
        
        async def generate_stream():
            try:
                # Queue to collect tool execution events
                tool_events = []
                
                def tool_stream_callback(event: ToolExecutionResponse):
                    """Callback to collect tool execution events"""
                    tool_events.append(event)
                
                # Get or create agent with streaming callback
                agent = get_or_create_agent(request.conversation_id or "default", tool_stream_callback)
                
                # Send start signal
                start_msg = StreamStartMessage()
                yield f"data: {start_msg.model_dump_json()}\n\n"
                
                # Create user message
                user_message = Message(role="user", content=request.message)
                
                # Run the agent conversation
                conversation = agent.run(user_message)
                
                try:
                    while True:
                        # Stream any pending tool events first
                        while tool_events:
                            event = tool_events.pop(0)
                            tool_msg = StreamToolExecutionMessage(
                                tool_name=event.tool_name,
                                status=event.status,
                                message=event.message,
                                progress=event.progress,
                                result=event.result,
                                error=event.error
                            )
                            yield f"data: {tool_msg.model_dump_json()}\n\n"
                        
                        result = next(conversation)
                        
                        if isinstance(result, ThinkingResponse):
                            # Stream thinking content as ephemeral messages for the thinking panel
                            if result.content:
                                for content_item in result.content:
                                    ephemeral_msg = StreamEphemeralMessage(content=content_item)
                                    yield f"data: {ephemeral_msg.model_dump_json()}\n\n"
                            
                            # Also stream summary if available
                            if result.summary:
                                for summary_item in result.summary:
                                    ephemeral_msg = StreamEphemeralMessage(content=f"Summary: {summary_item}")
                                    yield f"data: {ephemeral_msg.model_dump_json()}\n\n"
                            
                        elif isinstance(result, ToolCallsResponse):
                            # Handle special tool results like display_items and add_product
                            for tool_output in result.tool_outputs:
                                # Find the corresponding tool call
                                tool_call = next((tc for tc in result.tool_calls if tc.call_id == tool_output.call_id), None)
                                
                                if tool_call and tool_call.name == "display_items":
                                    # Parse display_items result
                                    try:
                                        import ast
                                        import asyncio
                                        
                                        # First try to get the raw structured result
                                        result_dict = None
                                        if result.raw_tool_results and tool_output.call_id in result.raw_tool_results:
                                            result_dict = result.raw_tool_results[tool_output.call_id]
                                        
                                        # Fallback to parsing the string output
                                        if not result_dict:
                                            output_str = tool_output.output
                                            if isinstance(output_str, str):
                                                try:
                                                    result_dict = ast.literal_eval(output_str)
                                                except (ValueError, SyntaxError):
                                                    try:
                                                        result_dict = json.loads(output_str)
                                                    except json.JSONDecodeError:
                                                        result_dict = {}
                                        
                                        if isinstance(result_dict, dict) and result_dict.get('success') and 'items' in result_dict:
                                                # Check if we should stream products individually
                                                if result_dict.get('stream_products', False):
                                                    # Stream each product individually with a small delay for better UX
                                                    for product in result_dict['items']:
                                                        product_msg = StreamProductMessage(product=product)
                                                        yield f"data: {product_msg.model_dump_json()}\n\n"
                                                        # Small delay between products for streaming effect
                                                        await asyncio.sleep(0.3)
                                                else:
                                                    # Stream as product grid message (all at once)
                                                    grid_msg = StreamProductGridMessage(
                                                        content=result_dict.get('message', ''),
                                                        products=result_dict['items'],
                                                        productGridTitle=result_dict.get('title', 'Product Recommendations')
                                                    )
                                                    yield f"data: {grid_msg.model_dump_json()}\n\n"
                                    except Exception as e:
                                        print(f"Error parsing display_items result: {e}")
                            # Continue processing normally
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
                            
                            message_msg = StreamMessageContent(content=response_text)
                            yield f"data: {message_msg.model_dump_json()}\n\n"
                            
                            # End the conversation since we don't expect user input in streaming
                            conversation.send(None)
                            break
                            
                except StopIteration:
                    # Conversation ended normally
                    pass
                
                # Stream any remaining tool events
                while tool_events:
                    event = tool_events.pop(0)
                    tool_msg = StreamToolExecutionMessage(
                        tool_name=event.tool_name,
                        status=event.status,
                        message=event.message,
                        progress=event.progress,
                        result=event.result,
                        error=event.error
                    )
                    yield f"data: {tool_msg.model_dump_json()}\n\n"
                
                # Send completion
                complete_msg = StreamCompleteMessage()
                yield f"data: {complete_msg.model_dump_json()}\n\n"
                
            except Exception as e:
                print(f"Error in stream: {str(e)}")
                import traceback
                traceback.print_exc()
                error_msg = StreamErrorMessage(error=str(e))
                yield f"data: {error_msg.model_dump_json()}\n\n"
        
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