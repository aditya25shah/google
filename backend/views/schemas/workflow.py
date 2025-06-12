from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel
from views.enums import WorkflowStatus


class WorkflowStep(BaseModel):
    action: str
    service: str
    status: str
    details: Dict[str, Any]
    timestamp: datetime


class Workflow(BaseModel):
    id: str
    user_name: str
    user_email: str
    title: str
    description: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    created_at: datetime
    updated_at: datetime
