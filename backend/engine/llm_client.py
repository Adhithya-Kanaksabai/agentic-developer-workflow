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


async def llm_complete(messages: list[dict], **kwargs) -> str:
    """
    Call the LLM with automatic fallback across free models.
    Returns the response content string.
    Raises RuntimeError if all models fail.
    """
    models = get_model_list()
    last_error = None

    for model in models:
        for attempt in range(2):  # 2 attempts per model before moving on
            try:
                print(f"[LLM Client] Attempting completion with model '{model}' (attempt {attempt+1})...", flush=True)
                response = await acompletion(
                    model=model,
                    messages=messages,
                    **kwargs,
                )
                print(f"[LLM Client] Success with model '{model}'", flush=True)
                return response.choices[0].message.content
            except (RateLimitError,) as e:
                print(f"[LLM Client] RateLimitError for model '{model}'. Retrying or falling back...", flush=True)
                last_error = e
                wait = 5 * (attempt + 1)
                await asyncio.sleep(wait)
                continue
            except (NotFoundError,) as e:
                print(f"[LLM Client] NotFoundError for model '{model}'. Skipping model...", flush=True)
                # Model doesn't exist, skip immediately
                last_error = e
                break
            except Exception as e:
                print(f"[LLM Client] Unexpected error for model '{model}': {e}", flush=True)
                last_error = e
                if attempt == 1:
                    break
                await asyncio.sleep(2)
        # If we got here via RateLimitError on both attempts, try next model

    raise RuntimeError(
        f"All LLM models failed. Last error: {last_error}"
    )
