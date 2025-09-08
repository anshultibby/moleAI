"""Tool registry for managing registered tools"""

from typing import Dict, List, Any, Optional
from app.models.chat import Tool


class ToolRegistry:
    """Registry for managing tool functions"""
    
    def __init__(self):
        self._tools: Dict[str, 'ToolFunction'] = {}
    
    def register(self, name: str, tool_func: 'ToolFunction') -> None:
        """Register a tool function in the registry"""
        self._tools[name] = tool_func
    
    def unregister(self, name: str) -> bool:
        """Unregister a tool function from the registry"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def get_tool(self, name: str) -> Optional['ToolFunction']:
        """Get a specific tool by name"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, 'ToolFunction']:
        """Get all registered tools"""
        return self._tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools"""
        return list(self._tools.keys())
    
    def clear(self) -> None:
        """Clear all registered tools (useful for testing)"""
        self._tools.clear()
    
    def to_openai_format(self) -> List[Tool]:
        """Convert all registered tools to OpenAI function calling format"""
        return [tool.to_openai_format() for tool in self._tools.values()]
    
    def execute_tool(self, name: str, context_vars: Dict[str, Any] = None, **kwargs) -> Any:
        """Execute a registered tool by name with given parameters and context variables"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry")
        
        return tool.execute(context_vars=context_vars, **kwargs)
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self._tools
    
    def count(self) -> int:
        """Get the number of registered tools"""
        return len(self._tools)


# Global registry instance
tool_registry = ToolRegistry()
