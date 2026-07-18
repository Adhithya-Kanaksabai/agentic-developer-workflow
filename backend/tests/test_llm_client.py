import pytest
from unittest.mock import AsyncMock, patch
from engine.llm_client import LLMClient
from events.bus import EventBus
from litellm.exceptions import RateLimitError

@pytest.mark.asyncio
async def test_llm_client_emits_events_on_success():
    bus = EventBus()
    bus.publish = AsyncMock()
    
    client = LLMClient(bus, "test_workflow")
    
    # Mock litellm acompletion to succeed instantly
    with patch("engine.llm_client.acompletion") as mock_acompletion:
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "success"
        mock_response.usage.total_tokens = 100
        mock_acompletion.return_value = mock_response
        
        result = await client.complete([{"role": "user", "content": "hello"}])
        
        assert result == "success"
        
        # Verify events
        assert bus.publish.call_count == 2
        
        event_1 = bus.publish.call_args_list[0][0][0]
        assert event_1.event_type == "LLMRequestStarted"
        assert event_1.workflow_id == "test_workflow"
        
        event_2 = bus.publish.call_args_list[1][0][0]
        assert event_2.event_type == "LLMRequestFinished"
        assert event_2.payload["total_tokens"] == 100

@pytest.mark.asyncio
async def test_llm_client_emits_fallback_event_on_ratelimit():
    bus = EventBus()
    bus.publish = AsyncMock()
    
    client = LLMClient(bus, "test_workflow")
    
    with patch("engine.llm_client.acompletion") as mock_acompletion, \
         patch("asyncio.sleep", new_callable=AsyncMock): # Don't actually sleep in tests
         
        # Make the first call fail with RateLimitError, second succeed
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "fallback success"
        mock_response.usage.total_tokens = 150
        
        # We need to mock a RateLimitError
        mock_acompletion.side_effect = [
            RateLimitError("Rate limited", llm_provider="test", model="test"),
            mock_response
        ]
        
        result = await client.complete([{"role": "user", "content": "hello"}])
        assert result == "fallback success"
        
        # Verify it emitted a failed event before succeeding on attempt 2
        assert bus.publish.call_count == 4
        assert bus.publish.call_args_list[0][0][0].event_type == "LLMRequestStarted"
        assert bus.publish.call_args_list[1][0][0].event_type == "LLMRequestFailed"
        assert bus.publish.call_args_list[2][0][0].event_type == "LLMRequestStarted" # attempt 2
        assert bus.publish.call_args_list[3][0][0].event_type == "LLMRequestFinished"
