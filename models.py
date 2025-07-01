from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    enable_tool_response: Optional[bool] = False

class ToolInfo(BaseModel):
    name: str
    args: str

class ToolResponse(BaseModel):
    name: str
    response: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_info: Optional[List[ToolInfo]] = []
    tool_response: Optional[List[ToolResponse]] = []

class SessionInfo(BaseModel):
    id: str
    created_at: datetime

class SessionHistory(SessionInfo):
    messages: List[Dict[str, Any]]