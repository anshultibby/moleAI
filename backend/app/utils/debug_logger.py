"""Debug logger for tracking tool execution"""

import os
import sys
from datetime import datetime
from functools import wraps

# Create debug directory if it doesn't exist
debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug')
os.makedirs(debug_dir, exist_ok=True)

# Create a debug log file with timestamp
log_file = os.path.join(debug_dir, f'debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

def debug_log(msg: str):
    """Write a debug message to both file and stdout"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_line = f"[{timestamp}] {msg}\n"
    
    # Write to file
    with open(log_file, 'a') as f:
        f.write(log_line)
        f.flush()
    
    # Write to stdout
    sys.stdout.write(log_line)
    sys.stdout.flush()

def log_execution(func):
    """Decorator to log function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        debug_log(f"\n{'='*50}")
        debug_log(f"Executing: {func.__name__}")
        debug_log(f"Args: {args}")
        debug_log(f"Kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            debug_log(f"Success: {func.__name__}")
            if isinstance(result, str):
                debug_log(f"Result: {result[:200]}...")
            return result
        except Exception as e:
            debug_log(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper 