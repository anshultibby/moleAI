# Progress Streaming Utilities
# Shared module to avoid circular imports

from .streaming_service import get_streaming_service

def set_streaming_callback(callback):
    """Set the callback function for streaming updates"""
    streaming_service = get_streaming_service()
    streaming_service.set_streaming_callback(callback)

def get_streaming_callback():
    """Get the current streaming callback function"""
    streaming_service = get_streaming_service()
    return streaming_service.get_streaming_callback()

# Global list to collect progress messages for streaming
_progress_messages = []

def add_progress_message(message: str):
    """Add a progress message to the global list"""
    global _progress_messages
    _progress_messages.append(message)

def get_and_clear_progress_messages():
    """Get all progress messages and clear the list"""
    global _progress_messages
    messages = _progress_messages.copy()
    _progress_messages.clear()
    return messages

def stream_progress_update(message: str):
    """Stream a progress update - only to console, NOT to frontend chat"""
    
    # Add to global progress messages for streaming
    add_progress_message(message)
    
    print(message) 