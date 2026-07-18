from abc import ABC, abstractmethod
from typing import Any
from engine.state import WorkflowState

class BaseStep(ABC):
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        pass

    def get_event_payload(self, state: WorkflowState) -> Any:
        return None
