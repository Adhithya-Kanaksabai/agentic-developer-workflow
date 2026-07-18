"""Quick end-to-end smoke test - runs Planner step only to verify API key + model work."""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from engine.state import WorkflowState
from steps.planner import PlannerStep

async def main():
    print(f"Using model: {os.getenv('DEFAULT_MODEL')}")
    state = WorkflowState(user_prompt="Build a simple Python calculator with add and subtract functions")
    planner = PlannerStep()
    print("Running Planner...")
    result = await planner.execute(state)
    print("SUCCESS! Spec generated:")
    print(result.spec.model_dump_json(indent=2))

asyncio.run(main())
