import json
from typing import Any
from engine.step import BaseStep
from engine.state import WorkflowState
from engine.llm_client import llm_complete, extract_json

class BuilderStep(BaseStep):
    def __init__(self, name: str = "Builder"):
        super().__init__(name)

    def get_event_payload(self, state: WorkflowState) -> Any:
        return state.artifacts

    async def execute(self, state: WorkflowState) -> WorkflowState:
        if not state.spec:
            raise ValueError("No specification found in state. Run Planner first.")

        system_prompt = (
            "You are a builder agent. Write the code files defined in the Specification.\n"
            f"Description: {state.spec.description}\n"
            f"Files to create: {state.spec.files_to_create}\n"
            f"Tasks: {state.spec.tasks}\n"
            f"Constraints: {state.spec.constraints}\n\n"
            "Output a single JSON object mapping each filename (key) to its complete code content (value).\n"
            "Example: {\"main.py\": \"print('hello')\", \"utils.py\": \"def add(a,b): return a+b\"}\n"
            "Output ONLY the raw JSON object. No markdown, no code fences, no extra text."
        )

        content = await llm_complete([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write the files for: {state.spec.model_dump_json()}"}
        ])

        raw = extract_json(content)
        files_dict = json.loads(raw)
        for filename, file_content in files_dict.items():
            state.artifacts[filename] = file_content

        state.logs.append(f"Builder completed: Generated {len(files_dict)} files.")
        return state
