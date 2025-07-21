# Progress Streaming Utilities
# Shared module to avoid circular imports

# Global variable to store streaming callback
_streaming_callback = None

def set_streaming_callback(callback):
    """Set the callback function for streaming updates"""
    global _streaming_callback
    _streaming_callback = callback

def get_streaming_callback():
    """Get the current streaming callback function"""
    global _streaming_callback
    return _streaming_callback

def stream_progress_update(message: str):
    """Stream a progress update - only to console, NOT to frontend chat"""
    global _streaming_callback
    
    # Add to global progress messages for streaming
    try:
        from .shopping_pipeline import add_progress_message
        add_progress_message(message)
    except ImportError:
        pass
    
    print(message) 