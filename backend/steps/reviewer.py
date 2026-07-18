from typing import Any
from engine.step import BaseStep
from engine.state import WorkflowState
from engine.llm_client import llm_complete

class ReviewerStep(BaseStep):
    def __init__(self, name: str = "Reviewer"):
        super().__init__(name)

    def get_event_payload(self, state: WorkflowState) -> Any:
        return state.logs[-1] if state.logs else None

    async def execute(self, state: WorkflowState) -> WorkflowState:
        if not state.spec or not state.artifacts:
            raise ValueError("Specification or Artifacts missing from state.")

        files_summary = "\n".join(
            f"--- {fname} ---\n{content[:800]}{'...(truncated)' if len(content) > 800 else ''}"
            for fname, content in state.artifacts.items()
        )

        system_prompt = (
            "You are a code reviewer. Evaluate the generated files against the Specification.\n"
            f"Specification: {state.spec.description}\n"
            f"Required files: {state.spec.files_to_create}\n"
            f"Constraints: {state.spec.constraints}\n\n"
            "Generated files:\n"
            f"{files_summary}\n\n"
            "Write a 2-4 sentence review. Start with 'Review Pass' if code meets requirements, "
            "or 'Review Fail' if not."
        )

        review_result = await llm_complete([
            {"role": "system", "content": system_prompt}
        ])

        state.logs.append(f"Reviewer completed: {review_result.strip()}")
        return state
