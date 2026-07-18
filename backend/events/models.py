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

class LLMRequestStarted(WorkflowEvent):
    event_type: str = "LLMRequestStarted"

class LLMRequestFailed(WorkflowEvent):
    event_type: str = "LLMRequestFailed"

class LLMRequestFinished(WorkflowEvent):
    event_type: str = "LLMRequestFinished"
