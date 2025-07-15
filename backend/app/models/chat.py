from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    deals_found: Optional[List[dict]] = None

class ChatHistory(BaseModel):
    messages: List[dict] 