from pydantic import BaseModel
from typing import Any, Optional

class WorkflowEvent(BaseModel):
    event_type: str
    workflow_id: str
    step_name: Optional[str] = None
    payload: Any = None
    
class WorkflowStarted(WorkflowEvent):
    event_type: str = "WorkflowStarted"

class StepStarted(WorkflowEvent):
    event_type: str = "StepStarted"

class StepFinished(WorkflowEvent):
    event_type: str = "StepFinished"
    
class WorkflowCompleted(WorkflowEvent):
    event_type: str = "WorkflowCompleted"

class WorkflowFailed(WorkflowEvent):
    event_type: str = "WorkflowFailed"
