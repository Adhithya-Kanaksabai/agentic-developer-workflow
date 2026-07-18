import asyncio
from typing import AsyncGenerator
from events.models import WorkflowEvent

class EventBus:
    def __init__(self):
        self._queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue()
        
    async def publish(self, event: WorkflowEvent):
        await self._queue.put(event)
        
    async def subscribe(self) -> AsyncGenerator[WorkflowEvent, None]:
        while True:
            event = await self._queue.get()
            yield event
            self._queue.task_done()
