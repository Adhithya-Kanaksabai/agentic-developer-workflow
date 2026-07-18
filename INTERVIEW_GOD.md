# Interview God File: Lively Hubble

This file documents the major engineering challenges, architectural decisions, and bug fixes throughout the development of Lively Hubble. It serves as a flagship portfolio piece.

## Problem: Fragile JSON Parsing in LLM Code Generation
**Problem**: The LLM agent was generating code enclosed within a JSON object using the format `{"file_name": "...", "code": "..."}`. However, when the LLM generated code containing double quotes, backslashes, or multiline strings (like in a python script with lots of functions or docstrings), the JSON parser would throw `invalid control character` errors or fail to parse entirely, breaking the entire pipeline.
**Solution**: Migrated from JSON-based code extraction to an XML-tag based extraction. The LLM was instructed to wrap code inside `<file name="...">...</file>` tags. A robust Python regex `re.findall(r'<file name="(.*?)">\s*(.*?)\s*</file>', content, re.DOTALL)` was implemented in the `BuilderStep` to reliably extract the files regardless of internal escaping or quote structures.
**Why**: XML/tag-based parsing is natively immune to internal string escaping issues that plague JSON. By using regex with `re.DOTALL`, we can capture the raw code precisely as output by the LLM without requiring the LLM to meticulously escape strings, fundamentally solving the pipeline crash.

## Problem: Internal IPC Buffer Overflows during Browser Subagent Verification
**Problem**: During testing with `clever-franklin` browser automation pipelines, the Antigravity backend would crash randomly and reset to the home screen.
**Solution**: Identified that the browser subagent was attempting to send massive video artifacts (7MB+ WebM recordings) over the internal IPC channel. The fix involved instructing the subagent to avoid returning large video artifacts or configuring the system to store them externally rather than piping them through IPC.
**Why**: Inter-Process Communication channels have strict buffer limits. Passing multi-megabyte binary streams through them directly causes overflows and immediate crashes. Storing on disk and passing the URI is the correct pattern.

## Problem: Building a Premium Reactive UI for Telemetry
**Problem**: The initial Vanilla HTML/JS implementation of the dashboard was functional but lacked a "premium" feel. It used standard emojis, jittery DOM updates for scrolling, and basic CSS. We needed a UI that could smoothly animate state transitions for the AI agent (e.g., streaming tokens, success/failure badges) and look like a world-class application.
**Solution**: Migrated the entire frontend to Vite + React + Tailwind CSS v4. Implemented Aceternity-inspired UI layouts with `framer-motion` for smooth `<AnimatePresence>` transitions. Used SVG icons from `lucide-react`. The FastAPI backend was updated to serve the compiled Vite static assets from `/frontend/dist`.
**Why**: To achieve a stunning, "goated" UI with micro-animations, a virtual DOM with a dedicated animation library (`framer-motion`) is necessary. Vanilla JS manipulation of DOM nodes becomes too complex to manage smoothly when dealing with real-time SSE telemetry streams coming from a multi-agent backend.
