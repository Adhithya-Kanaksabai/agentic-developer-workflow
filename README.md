# Developer Workflow Orchestrator (Software Factory)

A production-grade, deterministic AI Developer Workflow Runtime.

## The Philosophy
Instead of relying on unpredictable "agentic loops" (like standard LangGraph implementations) where an LLM is the brain routing the application, this project treats the **Workflow** as the product. AI agents are merely interchangeable workers inside a deterministic, hardcoded pipeline.

## Architecture (V1)
* **Core Engine:** A deterministic Python DAG runtime (`WorkflowRuntime`) that executes steps sequentially.
* **Steps:** 
  * `PlannerStep`: Reads user input, generates a structured technical `Specification` (the source of truth).
  * `BuilderStep`: Reads the `Specification` and generates raw code files.
  * `ReviewerStep`: Evaluates the generated files against the constraints in the `Specification`.
* **Event Streaming:** An asynchronous `EventBus` that streams Pydantic events (e.g., `StepStarted`, `StepFinished`) to the frontend via Server-Sent Events (SSE).
* **Resilient LLM Client:** A custom async LiteLLM wrapper with automatic fallback across multiple models to gracefully handle rate limits and upstream API failures.

## Getting Started

1. Clone the repo and navigate to `backend/`.
2. Add your OpenRouter API key to `backend/.env`.
3. Start the backend:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```
4. Open `frontend/index.html` in your browser.
