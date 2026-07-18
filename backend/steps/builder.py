import re
from typing import Any
from engine.step import BaseStep
from engine.state import WorkflowState

class BuilderStep(BaseStep):
    def __init__(self, name: str = "Builder"):
        super().__init__(name)

    def get_event_payload(self, state: WorkflowState) -> Any:
        return state.artifacts

    async def execute(self, state: WorkflowState, llm_client: Any) -> WorkflowState:
        if not state.spec:
            raise ValueError("BuilderStep requires a Specification in state.")

        system_prompt = (
            "You are a master software builder. Given a Specification, generate all required code files.\n"
            "Output each file wrapped in XML tags like this:\n"
            "<file name=\"main.py\">\nprint('hello')\n</file>\n"
            "Do NOT output JSON. Just output the XML blocks."
        )

        content = await llm_client.complete([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write the files for: {state.spec.model_dump_json()}"}
        ])

        # Parse XML blocks
        matches = re.findall(r'<file name="([^"]+)">\s*(.*?)\s*</file>', content, re.DOTALL)
        files_dict = {filename: file_content for filename, file_content in matches}
        
        for filename, file_content in files_dict.items():
            state.artifacts[filename] = file_content

        state.logs.append(f"Builder completed: Generated {len(files_dict)} files.")
        return state
