import json
from typing import Any
from engine.step import BaseStep
from engine.state import WorkflowState, Specification
from engine.llm_client import extract_json

class PlannerStep(BaseStep):
    def __init__(self, name: str = "Planner"):
        super().__init__(name)

    def get_event_payload(self, state: WorkflowState) -> Any:
        return state.spec.model_dump() if state.spec else None

    async def execute(self, state: WorkflowState, llm_client: Any) -> WorkflowState:
        print("Running Planner...", flush=True)
        
        messages = [
            {"role": "system", "content": "You are a senior software architect. Given a user prompt, generate a technical specification. The specification MUST be valid JSON conforming exactly to the following structure:\n\n{\n  \"description\": \"Overall description of what to build\",\n  \"tasks\": [\"Task 1\", \"Task 2\"],\n  \"files_to_create\": [\"file1.py\", \"file2.js\"],\n  \"constraints\": [\"Constraint 1\", \"Constraint 2\"]\n}\n\nDo not include any explanation outside of the JSON block."},
            {"role": "user", "content": state.user_prompt}
        ]
        
        content = await llm_client.complete(messages=messages)

        raw = extract_json(content)
        spec_dict = json.loads(raw, strict=False)
        state.spec = Specification(**spec_dict)
        state.logs.append("Planner completed: Technical specification generated.")
        return state
