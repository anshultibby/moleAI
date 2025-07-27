from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from pydantic import BaseModel


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolCallList(BaseModel):
    tool_calls: List[ToolCall]


@dataclass
class Tool:
    """A function that can be called by the agent"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any] = None
    
    def call(self, **kwargs) -> str:
        """Execute the tool function with given arguments"""
        try:
            if self.parameters:
                # Validate parameters if defined
                for param, config in self.parameters.items():
                    if config.get('required', False) and param not in kwargs:
                        raise ValueError(f"Required parameter '{param}' missing")
            
            result = self.function(**kwargs)
            return str(result) if result is not None else "Function executed successfully"
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}" 