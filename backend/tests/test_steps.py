import pytest
from unittest.mock import patch, MagicMock
from engine.state import WorkflowState, Specification
from steps.planner import PlannerStep
from steps.builder import BuilderStep
from steps.reviewer import ReviewerStep

# Mock response structure for litellm.completion
def create_mock_litellm_response(content: str):
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response

@pytest.mark.asyncio
@patch("steps.planner.completion")
async def test_planner_step(mock_completion):
    # Mocking completion response returning a serialized Specification JSON
    mock_spec_json = '{"description": "Build a Todo API", "tasks": ["Setup DB", "Create Routes"], "files_to_create": ["main.py", "db.py"], "constraints": ["Use FastAPI"]}'
    mock_completion.return_value = create_mock_litellm_response(mock_spec_json)
    
    state = WorkflowState(user_prompt="Build a Todo API with FastAPI")
    step = PlannerStep()
    
    final_state = await step.execute(state)
    
    assert final_state.spec is not None
    assert final_state.spec.description == "Build a Todo API"
    assert "Setup DB" in final_state.spec.tasks
    assert "main.py" in final_state.spec.files_to_create
    assert mock_completion.called

@pytest.mark.asyncio
@patch("steps.builder.completion")
async def test_builder_step(mock_completion):
    # Mocking completion response returning file contents in a structured JSON
    # The Builder should return a JSON dict mapping filenames to their contents.
    mock_files_json = '{"main.py": "print(\'hello\')", "db.py": "class DB: pass"}'
    mock_completion.return_value = create_mock_litellm_response(mock_files_json)
    
    spec = Specification(description="Build dummy files", files_to_create=["main.py", "db.py"])
    state = WorkflowState(spec=spec)
    step = BuilderStep()
    
    final_state = await step.execute(state)
    
    assert "main.py" in final_state.artifacts
    assert final_state.artifacts["main.py"] == "print('hello')"
    assert "db.py" in final_state.artifacts
    assert final_state.artifacts["db.py"] == "class DB: pass"
    assert mock_completion.called

@pytest.mark.asyncio
@patch("steps.reviewer.completion")
async def test_reviewer_step(mock_completion):
    # Mocking reviewer evaluation response
    mock_completion.return_value = create_mock_litellm_response("Review Pass: All files created correctly and follow constraints.")
    
    spec = Specification(description="Build dummy files", files_to_create=["main.py"])
    state = WorkflowState(spec=spec, artifacts={"main.py": "print('hello')"})
    step = ReviewerStep()
    
    final_state = await step.execute(state)
    
    assert len(final_state.logs) > 0
    assert any("Review Pass" in log for log in final_state.logs)
    assert mock_completion.called
