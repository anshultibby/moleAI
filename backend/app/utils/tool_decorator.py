"""Tool decorator system for creating agent tools"""

import inspect
from typing import Dict, Optional, Callable, TypeVar, cast
from functools import wraps
from dataclasses import dataclass
from ..modules.agent import Tool

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

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, ToolParameter]] = None
) -> Callable[[F], F]:
    """
    Decorator to convert a function into a tool that can be used by an agent.
    
    Usage:
        @tool(
            name="search",
            description="Search for something",
            parameters={
                "query": ToolParameter(
                    type="string",
                    description="Search query",
                    required=True
                )
            }
        )
        def search_function(query: str) -> str:
            return f"Searching for {query}"
    
    If name/description/parameters are not provided, they will be inferred from
    the function's name, docstring, and type hints.
    """
    def decorator(func: F) -> F:
        # Get function's signature
        sig = inspect.signature(func)
        
        # Store tool metadata on the function
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Execute {tool_name}"
        
        # Build parameters from function signature if not provided
        tool_parameters = parameters or {}
        if not tool_parameters:
            for param_name, param in sig.parameters.items():
                # Skip self for methods
                if param_name == 'self':
                    continue
                    
                param_type = "string"  # default
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == str:
                        param_type = "string"
                    elif param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list:
                        param_type = "array"
                    elif param.annotation == dict:
                        param_type = "object"
                
                tool_parameters[param_name] = ToolParameter(
                    type=param_type,
                    description=f"Parameter {param_name}",
                    required=param.default == inspect.Parameter.empty
                )
        
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

def create_tool(func: Callable) -> 'Tool':
    
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