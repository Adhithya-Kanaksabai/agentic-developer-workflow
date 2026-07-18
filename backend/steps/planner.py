import json
from typing import Any
from engine.step import BaseStep
from engine.state import WorkflowState, Specification
from engine.llm_client import llm_complete, extract_json

class PlannerStep(BaseStep):
    def __init__(self, name: str = "Planner"):
        super().__init__(name)

    def get_event_payload(self, state: WorkflowState) -> Any:
        return state.spec.model_dump() if state.spec else None

    async def execute(self, state: WorkflowState) -> WorkflowState:
        system_prompt = (
            "You are a technical planner agent. Analyze the user request and output a Specification as JSON.\n"
            "The JSON must have EXACTLY these keys:\n"
            '- "description": string describing the goal.\n'
            '- "tasks": list of strings detailing subtasks.\n'
            '- "files_to_create": list of filename strings.\n'
            '- "constraints": list of constraint strings.\n'
            "Output ONLY the raw JSON object. No markdown, no code fences, no extra text."
        )

        content = await llm_complete([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state.user_prompt}
        ])

        raw = extract_json(content)
        spec_dict = json.loads(raw)
        state.spec = Specification(**spec_dict)
        state.logs.append("Planner completed: Technical specification generated.")
        return state
