from typing import List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    message: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    workflow_id: Optional[str] = None
    actions_taken: List[str] = []
