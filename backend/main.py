import asyncio
import os
import uuid
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

from engine.state import WorkflowState
from engine.runtime import Workflow, WorkflowRuntime
from events.bus import EventBus
from workflows.definitions import feature_v1_workflow

app = FastAPI(title="AI Developer Workflow Engine")

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active job event buses
active_jobs: Dict[str, EventBus] = {}

class RunWorkflowRequest(BaseModel):
    prompt: str

async def execute_workflow(job_id: str, prompt: str, bus: EventBus):
    runtime = WorkflowRuntime(bus)
    initial_state = WorkflowState(user_prompt=prompt)
    try:
        await runtime.run(feature_v1_workflow, initial_state)
    except Exception as e:
        # Import inside function to avoid circular dependencies
        from events.models import WorkflowEvent
        error_event = WorkflowEvent(
            event_type="WorkflowFailed",
            workflow_id=job_id,
            payload={"error": str(e)}
        )
        await bus.publish(error_event)
    finally:
        # Schedule cleanup of the active job bus after 5 minutes
        await asyncio.sleep(300)
        active_jobs.pop(job_id, None)

@app.post("/api/workflows/run")
async def run_workflow(request: RunWorkflowRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    bus = EventBus()
    active_jobs[job_id] = bus
    
    background_tasks.add_task(execute_workflow, job_id, request.prompt, bus)
    
    return {"job_id": job_id}

@app.get("/api/workflows/{job_id}/stream")
async def stream_workflow(job_id: str):
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found or already completed")
        
    bus = active_jobs[job_id]
    
    async def event_generator():
        try:
            async for event in bus.subscribe():
                yield f"data: {event.model_dump_json()}\n\n"
                if event.event_type in ("WorkflowCompleted", "WorkflowFailed"):
                    break
        except asyncio.CancelledError:
            # Client closed the connection
            pass
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

from fastapi.staticfiles import StaticFiles
import os

# Get absolute path to frontend directory assuming main.py is in backend/
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
