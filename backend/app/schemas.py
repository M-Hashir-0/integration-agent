from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class IntegrationCreate(BaseModel):
    name: str
    spec_url: str
    api_key: Optional[str] = None


class IntegrationResponse(BaseModel):
    message: str
    tools_count: int


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    tool_calls: List[Dict[str, Any]] = []
