import pytest
import asyncio
from events.bus import EventBus
from events.models import WorkflowStarted

@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    
    events_received = []
    
    async def consumer():
        async for event in bus.subscribe():
            events_received.append(event)
            if len(events_received) == 2:
                break
                
    task = asyncio.create_task(consumer())
    
    event1 = WorkflowStarted(workflow_id="123")
    event2 = WorkflowStarted(workflow_id="123")
    
    await bus.publish(event1)
    await bus.publish(event2)
    
    await asyncio.wait_for(task, timeout=1.0)
    
    assert len(events_received) == 2
    assert events_received[0] == event1
    assert events_received[1] == event2
