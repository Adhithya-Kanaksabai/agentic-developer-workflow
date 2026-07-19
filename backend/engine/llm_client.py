"""
LLM client wrapper with multi-model fallback for free OpenRouter tier.
If the primary model is rate-limited, automatically tries the next one.
"""
import os
import asyncio
import re
from litellm import acompletion
from litellm.exceptions import RateLimitError, NotFoundError

# Ordered fallback list — best to worst for JSON-heavy tasks
FREE_MODEL_FALLBACKS = [
    "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    "openrouter/google/gemma-4-31b-it:free",
    "openrouter/google/gemma-4-26b-a4b-it:free",
    "openrouter/meta-llama/llama-3.2-3b-instruct:free",
    "openrouter/nousresearch/hermes-3-llama-3.1-405b:free",
    "openrouter/qwen/qwen3-coder:free",
]


def get_model_list() -> list[str]:
    """Return model list: env var first, then fallbacks."""
    primary = os.getenv("DEFAULT_MODEL")
    if primary and primary not in FREE_MODEL_FALLBACKS:
        return [primary] + FREE_MODEL_FALLBACKS
    return FREE_MODEL_FALLBACKS


def extract_json(text: str) -> str:
    """Strip markdown code fences and return raw JSON string."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)```$", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    # Find first { ... } block if no fence
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text


class LLMClient:
    def __init__(self, event_bus, workflow_id: str):
        self.event_bus = event_bus
        self.workflow_id = workflow_id
        self.current_step = None
        
    async def complete(self, messages: list[dict], **kwargs) -> str:
        from events.models import LLMRequestStarted, LLMRequestFailed, LLMRequestFinished
        
        models = get_model_list()
        last_error = None

        for model in models:
            for attempt in range(2):
                try:
                    await self.event_bus.publish(LLMRequestStarted(
                        workflow_id=self.workflow_id,
                        step_name=self.current_step,
                        payload={"model": model, "attempt": attempt + 1}
                    ))
                    
                    response = await acompletion(
                        model=model,
                        messages=messages,
                        **kwargs,
                    )
                    
                    tokens = getattr(response.usage, "total_tokens", 0) if hasattr(response, "usage") else 0
                    
                    await self.event_bus.publish(LLMRequestFinished(
                        workflow_id=self.workflow_id,
                        step_name=self.current_step,
                        payload={"model": model, "total_tokens": tokens}
                    ))
                    
                    return response.choices[0].message.content
                except (RateLimitError,) as e:
                    await self.event_bus.publish(LLMRequestFailed(
                        workflow_id=self.workflow_id,
                        step_name=self.current_step,
                        payload={"model": model, "error": "RateLimitError"}
                    ))
                    last_error = e
                    wait = 5 * (attempt + 1)
                    await asyncio.sleep(wait)
                    continue
                except (NotFoundError,) as e:
                    await self.event_bus.publish(LLMRequestFailed(
                        workflow_id=self.workflow_id,
                        step_name=self.current_step,
                        payload={"model": model, "error": "NotFoundError"}
                    ))
                    last_error = e
                    break
                except Exception as e:
                    await self.event_bus.publish(LLMRequestFailed(
                        workflow_id=self.workflow_id,
                        step_name=self.current_step,
                        payload={"model": model, "error": str(e)}
                    ))
                    last_error = e
                    if attempt == 1:
                        break
                    await asyncio.sleep(2)

        raise RuntimeError(f"All LLM models failed. Last error: {last_error}")
