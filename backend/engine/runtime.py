import uuid
from dataclasses import dataclass
from typing import List
from engine.state import WorkflowState
from engine.step import BaseStep
from events.bus import EventBus
from events.models import WorkflowStarted, StepStarted, StepFinished, WorkflowCompleted

@dataclass
class Workflow:
    name: str
    steps: List[BaseStep]

class WorkflowRuntime:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
    async def run(self, workflow: Workflow, initial_state: WorkflowState) -> WorkflowState:
        workflow_id = str(uuid.uuid4())
        state = initial_state
        
        from engine.llm_client import LLMClient
        llm_client = LLMClient(self.event_bus, workflow_id)
        
        print(f"\n[WorkflowRuntime] Starting workflow '{workflow.name}' (ID: {workflow_id})", flush=True)
        # Publish WorkflowStarted
        await self.event_bus.publish(WorkflowStarted(workflow_id=workflow_id))
        
        # Execute steps in order
        for step in workflow.steps:
            print(f"[WorkflowRuntime] Starting step: {step.name}", flush=True)
            # Publish StepStarted
            await self.event_bus.publish(StepStarted(workflow_id=workflow_id, step_name=step.name))
            
            # Execute step
            llm_client.current_step = step.name
            state = await step.execute(state, llm_client)
            
            # Get event payload generically
            payload = step.get_event_payload(state)
            
            print(f"[WorkflowRuntime] Finished step: {step.name}", flush=True)
            # Publish StepFinished
            await self.event_bus.publish(StepFinished(workflow_id=workflow_id, step_name=step.name, payload=payload))
            
        print(f"[WorkflowRuntime] Completed workflow '{workflow.name}'\n", flush=True)
        # Publish WorkflowCompleted
        await self.event_bus.publish(WorkflowCompleted(workflow_id=workflow_id))
        
        return state
