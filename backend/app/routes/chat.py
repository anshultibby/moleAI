"""Chat routes for the shopping deals agent"""

import ast
import asyncio
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from enum import Enum

from app.modules.agent import Agent
from app.models import (
    Message, ThinkingResponse, ToolCallsResponse, AssistantResponse, ToolExecutionResponse,
    OpenAIResponse, ResponseOutputMessage, StreamStartMessage, StreamMessageContent,
    StreamProductMessage, StreamProductGridMessage, StreamEphemeralMessage,
    StreamToolExecutionMessage, StreamCompleteMessage, StreamErrorMessage, StreamTurnLimitMessage
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
llm_router = LLMRouter(
    openai_api_key=OPENAI_API_KEY,
    xlm_api_key=XLM_API_KEY
)

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

def end_conversation_tracking(conversation_id: str, user_message: str, agent: Agent) -> None:
    """Helper method to mark conversation as ended"""
    try:
        conversation_id_to_save = conversation_id or "default"
        
        # Create final metadata about the conversation
        metadata = {
            "final_user_message": user_message,
            "model": agent.model,
            "reasoning_effort": agent.reasoning_effort,
            "total_messages": len(agent.get_message_history())
        }
        
        # Mark conversation as ended
        chat_storage.end_conversation(
            conversation_id=conversation_id_to_save,
            metadata=metadata
        )
        print(f"Ended conversation tracking: {conversation_id_to_save}")
        
    except Exception as e:
        print(f"Error ending conversation tracking: {e}")
        # Don't fail the request if ending fails

async def stream_tool_events(tool_events: List[ToolExecutionResponse]):
    """Helper to stream pending tool events"""
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

async def handle_thinking_response(result: ThinkingResponse):
    """Helper to handle thinking response streaming"""
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

async def handle_display_items_tool(tool_output, result: ToolCallsResponse):
    """Helper to handle display_items tool results"""
    try:
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

def extract_assistant_response_text(result: AssistantResponse) -> str:
    """Helper to extract text from assistant response"""
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
    
    return response_text

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
            try:
                # Queue to collect tool execution events
                tool_events = []
                
                def tool_stream_callback(event: ToolExecutionResponse):
                    """Callback to collect tool execution events"""
                    tool_events.append(event)
                
                # Get or create agent with streaming callback
                agent = get_or_create_agent(request.conversation_id or "default", tool_stream_callback, request.model)
                
                # Check turn limit before processing the message
                is_exceeded, current_turns = agent.is_turn_limit_exceeded(max_turns=40)
                if is_exceeded:
                    turn_limit_msg = StreamTurnLimitMessage(
                        message=f"Conversation has reached the maximum limit of 40 turns. Current turns: {current_turns}. Please start a new conversation.",
                        current_turns=current_turns,
                        max_turns=40
                    )
                    yield f"data: {turn_limit_msg.model_dump_json()}\n\n"
                    
                    # Send completion to end the stream
                    complete_msg = StreamCompleteMessage()
                    yield f"data: {complete_msg.model_dump_json()}\n\n"
                    return
                
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
                        async for item in stream_tool_events(tool_events):
                            yield item
                        
                        result = next(conversation)
                        
                        if isinstance(result, ThinkingResponse):
                            async for item in handle_thinking_response(result):
                                yield item
                            
                        elif isinstance(result, ToolCallsResponse):
                            # Handle special tool results like display_items and add_product
                            for tool_output in result.tool_outputs:
                                # Find the corresponding tool call
                                tool_call = next((tc for tc in result.tool_calls if tc.call_id == tool_output.call_id), None)
                                
                                if tool_call and tool_call.name == "display_items":
                                    async for item in handle_display_items_tool(tool_output, result):
                                        yield item
                            # Continue processing normally
                            pass
                            
                        elif isinstance(result, AssistantResponse):
                            # Stream the assistant response using helper
                            response_text = extract_assistant_response_text(result)
                            message_msg = StreamMessageContent(content=response_text)
                            yield f"data: {message_msg.model_dump_json()}\n\n"
                            
                            # Save assistant message to chat history with finish_reason
                            if response_text.strip():  # Only save if there's actual content
                                assistant_message = Message(
                                    role="assistant",
                                    content=response_text,
                                    finish_reason=getattr(result.response, 'finish_reason', None)
                                )
                                agent.add_to_history(assistant_message)
                            
                            # Check if conversation should end based on finish_reason
                            if (hasattr(result.response, 'finish_reason') and 
                                result.response.finish_reason == 'stop'):
                                # End the conversation when finish_reason is 'stop'
                                conversation.send(None)
                                break
                            else:
                                # Continue conversation for other finish_reasons like 'tool_calls'
                                conversation.send(None)
                            
                except StopIteration:
                    # Conversation ended normally
                    pass
                
                # Stream any remaining tool events
                async for item in stream_tool_events(tool_events):
                    yield item
                
                # End conversation tracking
                end_conversation_tracking(request.conversation_id, request.message, agent)
                
                # Send completion
                complete_msg = StreamCompleteMessage()
                yield f"data: {complete_msg.model_dump_json()}\n\n"
                
            except Exception as e:
                print(f"Error in stream: {str(e)}")
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
        provider_info = llm_router.get_provider_info()
        all_models = llm_router.get_all_supported_models()
        
        return {
            "available_models": [model.value for model in AvailableModels],
            "providers": provider_info,
            "default_model": AvailableModels.GLM_4_5V.value,
            "model_descriptions": {
                AvailableModels.GLM_4_5V.value: "GLM-4.5V - XLM Vision Model (Z.AI)",
                AvailableModels.GPT_5.value: "GPT-5 - OpenAI Latest Model"
            }
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))