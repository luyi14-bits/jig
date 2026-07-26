# Multi-Model + Streaming PRD

## 1. Executive Summary
Add multi-model provider support (OpenAI, Anthropic, Ollama) and streaming output (SSE) to Jig's SOP pipeline.

## 2. Problem Statement
Currently Jig is locked to DeepSeek only. Users need multi-model flexibility. Streaming is required for real-time UX.

## 3. Functional Requirements
- FR-1: BaseModelProvider abstraction (existing, needs completion)
- FR-2: OpenAIProvider with full chat/stream support
- FR-3: ModelRouter consolidated (unify `model_router.py` + `model_provider.py`)
- FR-4: SSE streaming via handle_stream() → run_stream() real pipeline
- FR-5: Provider auto-discovery (env var based)

## 4. Out of Scope
- Anthropic/Ollama providers — add after OpenAI
- Streaming WebSocket — SSE only for v1
