"""Tool decorator for converting functions into OpenAI-compatible tools"""

import json
import inspect
from typing import Any, Dict, List, Optional, Callable, get_type_hints, get_origin, get_args
from functools import wraps
from loguru import logger
from app.tools.registry import tool_registry
from app.models.chat import Tool, FunctionObject, FunctionParameters


def _python_type_to_json_schema(py_type: Any, description: str = "") -> Dict[str, Any]:
    """Convert Python type hints to JSON schema format"""
    
    # Handle Optional types (Union[T, None])
    origin = get_origin(py_type)
    if origin is not None:
        args = get_args(py_type)
        
        # Handle Optional[T] which is Union[T, None]
        if origin is type(None) or (hasattr(py_type, '__module__') and py_type.__module__ == 'typing'):
            if len(args) == 2 and type(None) in args:
                # This is Optional[T]
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return _python_type_to_json_schema(non_none_type, description)
        
        # Handle List[T]
        if origin is list:
            if args:
                item_schema = _python_type_to_json_schema(args[0])
                return {
                    "type": "array",
                    "items": item_schema,
                    "description": description
                }
            else:
                return {"type": "array", "description": description}
    
    # Handle basic types
    if py_type is str:
        return {"type": "string", "description": description}
    elif py_type is int:
        return {"type": "integer", "description": description}
    elif py_type is float:
        return {"type": "number", "description": description}
    elif py_type is bool:
        return {"type": "boolean", "description": description}
    elif py_type is list:
        return {"type": "array", "description": description}
    elif py_type is dict:
        return {"type": "object", "description": description}
    else:
        # Default to string for unknown types
        return {"type": "string", "description": description}




class ToolFunction:
    """Represents a tool function with OpenAI compatibility"""
    
    def __init__(self, func: Callable, name: str = None, description: str = None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or ""
        self.signature = inspect.signature(func)
        self.type_hints = get_type_hints(func)
    
    def to_openai_format(self) -> Tool:
        """Convert the function to OpenAI function calling format"""
        
        properties = {}
        required = []
        
        for param_name, param in self.signature.parameters.items():
            # Skip 'self' parameter and context_vars parameter
            if param_name == 'self' or param_name == 'context_vars':
                continue
                
            # Get type hint
            param_type = self.type_hints.get(param_name, str)
            
            # Convert to JSON schema
            param_schema = _python_type_to_json_schema(param_type, f"The {param_name} parameter")
            properties[param_name] = param_schema
            
            # Check if parameter is required (no default value and not Optional)
            if param.default is inspect.Parameter.empty:
                # Check if it's Optional type
                origin = get_origin(param_type)
                if origin is not None:
                    args = get_args(param_type)
                    # If it's Union[T, None] (Optional), it's not required
                    if not (len(args) == 2 and type(None) in args):
                        required.append(param_name)
                else:
                    required.append(param_name)
        
        # Create the function parameters
        function_params = FunctionParameters(
            type="object",
            properties=properties,
            required=required
        )
        
        # Create the function object
        function_obj = FunctionObject(
            name=self.name,
            description=self.description,
            parameters=function_params
        )
        
        # Create the tool schema
        tool_schema = Tool(
            function=function_obj
        )
        
        return tool_schema
    
    def execute(self, context_vars: Dict[str, Any] = None, **kwargs) -> Any:
        """Execute the function with given parameters and context variables"""
        try:
            import asyncio
            import inspect
            
            context_vars = context_vars or {}
            
            # Check if the function accepts context_vars parameter
            function_params = set(self.signature.parameters.keys())
            
            # If function accepts context_vars, pass it as a named parameter
            if 'context_vars' in function_params:
                kwargs['context_vars'] = context_vars
            
            # Remove any extra parameters that the function doesn't accept
            # (for backward compatibility with old _agent parameter)
            kwargs = {k: v for k, v in kwargs.items() if k in function_params}
            
            # Validate parameters against signature
            bound_args = self.signature.bind(**kwargs)
            bound_args.apply_defaults()
            
            # Check if the function is async
            if inspect.iscoroutinefunction(self.func):
                # Handle async function
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, we need to run this in a thread pool
                    # to avoid blocking the event loop
                    import concurrent.futures
                    import threading
                    
                    def run_in_thread():
                        # Create a new event loop for this thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(self.func(**bound_args.arguments))
                        finally:
                            new_loop.close()
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        return future.result()
                except RuntimeError:
                    # No event loop running, we can use asyncio.run directly
                    return asyncio.run(self.func(**bound_args.arguments))
            else:
                # Execute sync function normally
                result = self.func(**bound_args.arguments)
                return result
            
        except TypeError as e:
            raise ValueError(f"Invalid parameters for {self.name}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error executing {self.name}: {str(e)}")


def tool(name: str = None, description: str = None):
    """
    Decorator to convert a function into an OpenAI-compatible tool.
    
    Args:
        name: Optional custom name for the tool (defaults to function name)
        description: Optional custom description (defaults to first line of docstring)
        Context variables are passed directly when calling the tool
    
    Example:
        @tool(name="get_weather", description="Get current weather for a location")
        def get_weather(location: str, units: str = "celsius") -> str:
            '''Get weather information for a location
            
            location: City and country e.g. Bogotá, Colombia
            units: Temperature units (celsius or fahrenheit)
            '''
            # Implementation here
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Create tool function wrapper
        tool_func = ToolFunction(func, name, description)
        
        # Register the tool
        tool_registry.register(tool_func.name, tool_func)
        
        # Return the original function with tool metadata
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Attach tool metadata to the wrapper
        wrapper._tool_func = tool_func
        wrapper._is_tool = True
        
        return wrapper
    
    return decorator
