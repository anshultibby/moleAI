from pydantic import BaseModel, model_validator
from typing import Literal, Optional, Dict, Any


class ResourceMetadata(BaseModel):
    content_type: Literal["text", "html"]
    length: int
    num_lines: int
    extra: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"ResourceMetadata(content_type={self.content_type}, length={self.length}, num_lines={self.num_lines})"
    
    def format_for_llm(self) -> str:
        """Format metadata for LLM without including the extra field"""
        return f"ResourceMetadata(content_type={self.content_type}, length={self.length}, num_lines={self.num_lines})"

class Resource(BaseModel):
    id: str
    content: str
    metadata: ResourceMetadata
    
    @model_validator(mode='before')
    @classmethod
    def set_num_lines(cls, values):
        """Automatically set num_lines in metadata based on content"""
        if isinstance(values, dict):
            content = values.get('content', '')
            if 'metadata' in values and isinstance(values['metadata'], dict):
                # Set num_lines if not already provided
                if 'num_lines' not in values['metadata']:
                    values['metadata']['num_lines'] = len(content.split('\n'))
        return values

    def format_for_llm(self, exclude_content: bool = False, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        if exclude_content:
            return f"Resource ID: {self.id}\nMetadata: {self.metadata.format_for_llm()}"
        else:
            lines = self.content.split('\n')
            
            # Handle line-based extraction
            if start_line is not None or end_line is not None:
                start = max(1, start_line if start_line is not None else 1) - 1  # Convert to 0-based index
                end = min(self.metadata.num_lines, end_line if end_line is not None else self.metadata.num_lines)  # Keep as 1-based for slicing
                
                selected_lines = lines[start:end]
                content = '\n'.join(selected_lines)
                content_info = f" (showing lines {start + 1}-{end} of {self.metadata.num_lines} total)"
            else:
                content = self.content
                content_info = ""
            
            return f"Resource ID: {self.id}\nContent{content_info}: {content}\nMetadata: {self.metadata.format_for_llm()}"

