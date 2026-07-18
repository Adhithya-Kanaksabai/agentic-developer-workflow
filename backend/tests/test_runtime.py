import pytest
from unittest.mock import AsyncMock
from engine.state import WorkflowState, Specification
from engine.step import BaseStep
from engine.runtime import Workflow, WorkflowRuntime
from events.bus import EventBus
from events.models import StepStarted, StepFinished, WorkflowStarted, WorkflowCompleted

class MockSuccessStep(BaseStep):
    def __init__(self, name: str):
        super().__init__(name)
        
    async def execute(self, state: WorkflowState) -> WorkflowState:
        # Mutate the state slightly to prove execution
        state.logs.append(f"Executed {self.name}")
        return state

@pytest.mark.asyncio
async def test_workflow_runtime_executes_ordered_steps():
    bus = EventBus()
    runtime = WorkflowRuntime(bus)
    
    # Define a simple workflow
    step1 = MockSuccessStep("Step 1")
    step2 = MockSuccessStep("Step 2")
    workflow = Workflow(name="Test Workflow", steps=[step1, step2])
    
    initial_state = WorkflowState()
    
    # Run the workflow
    final_state = await runtime.run(workflow, initial_state)
    
    # Verify order of execution in logs
    assert final_state.logs == ["Executed Step 1", "Executed Step 2"]

@pytest.mark.asyncio
async def test_workflow_runtime_publishes_events():
    bus = EventBus()
    runtime = WorkflowRuntime(bus)
    
    # Consume events in a background task
    events_received = []
    async def event_consumer():
        async for event in bus.subscribe():
            events_received.append(event)
            # Expecting 6 events: WorkflowStarted, StepStarted(1), StepFinished(1), StepStarted(2), StepFinished(2), WorkflowCompleted
            if len(events_received) == 6:
                break
                
    import asyncio
    consumer_task = asyncio.create_task(event_consumer())
    
    step1 = MockSuccessStep("Step 1")
    step2 = MockSuccessStep("Step 2")
    workflow = Workflow(name="Test Workflow", steps=[step1, step2])
    
    await runtime.run(workflow, WorkflowState())
    
    await asyncio.wait_for(consumer_task, timeout=1.0)
    
    assert len(events_received) == 6
    assert isinstance(events_received[0], WorkflowStarted)
    assert isinstance(events_received[1], StepStarted)
    assert events_received[1].step_name == "Step 1"
    assert isinstance(events_received[2], StepFinished)
    assert events_received[2].step_name == "Step 1"
    assert isinstance(events_received[3], StepStarted)
    assert events_received[3].step_name == "Step 2"
    assert isinstance(events_received[4], StepFinished)
    assert events_received[4].step_name == "Step 2"
    assert isinstance(events_received[5], WorkflowCompleted)
