"""Tool decorator system for creating agent tools"""

import inspect
from typing import Dict, Optional, Callable, TypeVar, cast, get_origin, get_args, Union
from functools import wraps
from dataclasses import dataclass
from .base import Tool

F = TypeVar('F', bound=Callable)

@dataclass
class ToolParameter:
    """Parameter definition for a tool"""
    type: str
    description: str
    required: bool = True

@dataclass
class ToolMetadata:
    """Metadata for a tool"""
    name: str
    description: str
    parameters: Dict[str, ToolParameter]

def _get_parameter_type(annotation) -> str:
    """Convert Python type annotation to JSON schema type string"""
    if annotation == inspect.Parameter.empty:
        return "string"  # default
    
    # Handle typing module types (Optional, Union, etc.)
    origin = get_origin(annotation)
    args = get_args(annotation)
    
    # Handle Optional[T] which is Union[T, None]
    if origin is Union:
        # Filter out NoneType to get the actual type
        non_none_args = [arg for arg in args if arg != type(None)]
        if len(non_none_args) == 1:
            # This is Optional[T], use the T type
            annotation = non_none_args[0]
        else:
            # Multiple non-None types, default to string
            return "string"
    
    # Handle basic types
    if annotation == str:
        return "string"
    elif annotation == int:
        return "integer"
    elif annotation == float:
        return "number"
    elif annotation == bool:
        return "boolean"
    elif annotation == list or get_origin(annotation) is list:
        return "array"
    elif annotation == dict or get_origin(annotation) is dict:
        return "object"
    else:
        # For any other type, default to string
        return "string"

def _is_parameter_required(param: inspect.Parameter) -> bool:
    """Determine if a parameter is required based on its default value"""
    return param.default == inspect.Parameter.empty

def _generate_parameter_description(param_name: str, param_type: str) -> str:
    """Generate a reasonable description for a parameter based on its name and type"""
    # Simple heuristics for common parameter names
    name_lower = param_name.lower()
    
    if 'query' in name_lower:
        return f"Search query or term"
    elif 'url' in name_lower:
        return f"URL or web address"
    elif 'name' in name_lower:
        return f"Name or title"
    elif 'price' in name_lower:
        return f"Price value"
    elif 'description' in name_lower:
        return f"Description or details"
    elif 'max' in name_lower or 'limit' in name_lower:
        return f"Maximum number or limit"
    elif 'image' in name_lower:
        return f"Image URL or path"
    elif 'product' in name_lower:
        return f"Product information"
    elif 'store' in name_lower:
        return f"Store name or identifier"
    elif 'category' in name_lower:
        return f"Category or classification"
    else:
        return f"The {param_name} parameter ({param_type})"

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, ToolParameter]] = None
) -> Callable[[F], F]:
    """
    Decorator to convert a function into a tool that can be used by an agent.
    
    Parameters are automatically extracted from the function signature.
    Manual parameter specification is optional and will override auto-detection.
    
    Usage:
        @tool
        def search_function(query: str, max_results: int = 5) -> str:
            return f"Searching for {query}"
        
        # Or with manual overrides:
        @tool(name="custom_search", description="Custom search tool")
        def search_function(query: str) -> str:
            return f"Searching for {query}"
    """
    def decorator(func: F) -> F:
        # Get function's signature
        sig = inspect.signature(func)
        
        # Store tool metadata on the function
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Execute {tool_name}"
        
        # Auto-build parameters from function signature
        auto_parameters = {}
        for param_name, param in sig.parameters.items():
            # Skip self for methods
            if param_name == 'self':
                continue
            
            param_type = _get_parameter_type(param.annotation)
            required = _is_parameter_required(param)
            param_description = _generate_parameter_description(param_name, param_type)
            
            auto_parameters[param_name] = ToolParameter(
                type=param_type,
                description=param_description,
                required=required
            )
        
        # Use manual parameters if provided, otherwise use auto-detected ones
        tool_parameters = parameters or auto_parameters
        
        # Store metadata on function
        setattr(func, '_tool_metadata', ToolMetadata(
            name=tool_name,
            description=tool_description,
            parameters=tool_parameters
        ))
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator

def get_tool_metadata(func: Callable) -> Optional[ToolMetadata]:
    """Get tool metadata from a decorated function"""
    return getattr(func, '_tool_metadata', None)

def create_tool(func: Callable) -> Tool:
    """Create a Tool instance from a decorated function"""
    metadata = get_tool_metadata(func)
    if not metadata:
        raise ValueError(f"Function {func.__name__} is not decorated with @tool")
    
    return Tool(
        name=metadata.name,
        description=metadata.description,
        function=func,
        parameters={
            name: {
                "type": param.type,
                "description": param.description,
                "required": param.required
            }
            for name, param in metadata.parameters.items()
        }
    ) 