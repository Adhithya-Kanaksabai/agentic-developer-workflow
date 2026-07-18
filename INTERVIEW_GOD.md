# The Interview God File 🧠

This document is the absolute source of truth for your technical interviews. It contains the "Why", "How", and "What" of this project. Review this before any System Design or AI Engineering interview.

## 1. The Core Problem We Are Solving
**Problem:** Most "AI Dev Agents" (like standard AutoGPT or basic LangGraph loops) are unreliable. They use an LLM as the "brain" to decide what to do next. This leads to infinite loops, hallucinations, and premature optimization.
**Solution:** A "Software Factory". We built a deterministic workflow engine in Python. The workflow itself (the code) decides the routing. The AI agents are just "workers" (functions) that take state in and return state out. 

## 2. Architecture & Tech Stack
- **Backend:** Python, FastAPI (for SSE streaming), LiteLLM (for multi-model orchestration), Pydantic (for strict data validation).
- **Frontend:** Vanilla HTML/CSS/JS (no heavy frameworks needed for V1) using Server-Sent Events (SSE) to consume real-time agent updates.
- **AI Integration:** OpenRouter API to route between top-tier free models (Llama 3 70B, Gemma).

## 3. Key Engineering Challenges & Solutions

### Challenge 1: The "Agentic Loop of Death"
* **Issue:** Early designs allowed a "Runner" agent to evaluate state and determine the next step. This is a massive anti-pattern for production AI because LLMs are non-deterministic routers.
* **Solution:** We strictly separated the **Control Flow** from the **Intelligence**. We built `WorkflowRuntime`, a rigid Python engine that executes a hardcoded array of `BaseStep` classes. The LLM is only invoked *inside* the step (e.g., `PlannerStep`, `BuilderStep`).

### Challenge 2: API Rate Limiting & Instability (OpenRouter)
* **Issue:** Free-tier AI models (like Gemma and Llama) are heavily rate-limited (HTTP 429) or unexpectedly removed (HTTP 404), causing pipeline crashes.
* **Solution:** Engineered a custom `llm_client.py` wrapper around `litellm`. It implements:
  - **Exponential Backoff:** Retries failed requests automatically.
  - **Multi-Model Fallback:** If a model 429s twice, it seamlessly catches the exception and falls back to the next model in a predefined array of 6 fallback models.

### Challenge 3: Unreliable JSON Output from OSS Models
* **Issue:** We needed the `Planner` to output a strict JSON Specification object so the `Builder` could parse it programmatically. However, open-source models often failed when forced into `response_format={"type": "json_object"}`.
* **Solution:** Removed the strict API-level JSON constraint. Instead, we heavily prompted the system prompt and wrote a robust Regex extractor `_extract_json()` in Python that reliably strips markdown code fences (` ```json `) and isolates the JSON payload.

## 4. Current State (V1)
- Implemented the deterministic engine.
- Implemented Planner -> Builder -> Reviewer workflow.
- Implemented real-time EventBus streaming to the UI.

## 5. Future Roadmap (V2+)
- **Sandboxed Execution:** Taking the generated artifacts in memory, writing them to disk, and actually executing them securely.
- **Automated Deployment:** Pushing verified code to a live environment.
