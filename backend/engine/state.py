from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class Specification(BaseModel):
    description: str
    tasks: List[str] = Field(default_factory=list)
    files_to_create: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

class WorkflowState(BaseModel):
    user_prompt: str = ""
    spec: Optional[Specification] = None
    artifacts: Dict[str, str] = Field(default_factory=dict)
    logs: List[str] = Field(default_factory=list)
