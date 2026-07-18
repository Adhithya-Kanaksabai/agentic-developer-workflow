import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from engine.state import WorkflowState, Specification
from steps.planner import PlannerStep
from steps.builder import BuilderStep
from steps.reviewer import ReviewerStep
from engine.llm_client import LLMClient

@pytest.fixture
def mock_llm_client():
    client = AsyncMock(spec=LLMClient)
    return client

@pytest.mark.asyncio
async def test_planner_step(mock_llm_client):
    mock_spec_json = '{"description": "Build a Todo API", "tasks": ["Setup DB", "Create Routes"], "files_to_create": ["main.py", "db.py"], "constraints": ["Use FastAPI"]}'
    mock_llm_client.complete.return_value = mock_spec_json
    
    state = WorkflowState(user_prompt="Build a Todo API with FastAPI")
    step = PlannerStep()
    
    final_state = await step.execute(state, mock_llm_client)
    
    assert final_state.spec is not None
    assert final_state.spec.description == "Build a Todo API"
    assert "Setup DB" in final_state.spec.tasks
    assert "main.py" in final_state.spec.files_to_create
    assert mock_llm_client.complete.called

@pytest.mark.asyncio
async def test_builder_step(mock_llm_client):
    mock_files_json = '{"main.py": "print(\'hello\')", "db.py": "class DB: pass"}'
    mock_llm_client.complete.return_value = mock_files_json
    
    spec = Specification(description="Build dummy files", files_to_create=["main.py", "db.py"])
    state = WorkflowState(spec=spec)
    step = BuilderStep()
    
    final_state = await step.execute(state, mock_llm_client)
    
    assert "main.py" in final_state.artifacts
    assert final_state.artifacts["main.py"] == "print('hello')"
    assert "db.py" in final_state.artifacts
    assert final_state.artifacts["db.py"] == "class DB: pass"
    assert mock_llm_client.complete.called

@pytest.mark.asyncio
async def test_reviewer_step(mock_llm_client):
    mock_llm_client.complete.return_value = "Review Pass: All files created correctly and follow constraints."
    
    spec = Specification(description="Build dummy files", files_to_create=["main.py"])
    state = WorkflowState(spec=spec, artifacts={"main.py": "print('hello')"})
    step = ReviewerStep()
    
    final_state = await step.execute(state, mock_llm_client)
    
    assert len(final_state.logs) > 0
    assert any("Review Pass" in log for log in final_state.logs)
    assert mock_llm_client.complete.called
