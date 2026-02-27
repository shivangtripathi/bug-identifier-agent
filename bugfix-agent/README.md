# BugFix Agent (LangGraph + PageIndex)

A dockerized multi-agent conversational bug-fixing system with:

- Planner + Executor agents orchestrated by LangGraph
- Structured tool calls with JSON output
- PageIndex-style semantic indexing (symbol-aware chunking; no vector DB)
- AST-safe code edits via `libcst` + unified diff preview
- Dependency impact analysis via `networkx`
- Permission-gated bash execution (`yes` required)
- Context compression for long conversations
- Model provider switching via env (`gemini` or `ollama`)
- LangSmith tracing hooks and tags

## Structure

```
bugfix-agent/
  agents/
  tools/
  demo_repo/
  tests/
  cli.py
  config.py
  Dockerfile
  README.md
```

## Run locally

```bash
pip install langchain langgraph langsmith langchain-google-genai langchain-community pageindex libcst networkx pytest typer rich pydantic
python cli.py chat --repo ./demo_repo
```

## Docker

```bash
docker build -t agent .
docker run -it -v $(pwd):/workspace agent
```

## Model switching

```bash
# Gemini
export LLM_PROVIDER=gemini
export GOOGLE_API_KEY=...
export GEMINI_MODEL=gemini-3-flash

# Ollama (Gemma)
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=gemma:2b
export OLLAMA_BASE_URL=http://localhost:11434
```

## LangSmith

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=...
export LANGSMITH_PROJECT=bugfix-agent
```

Each run adds tags including provider and bug id in the orchestrator invoke config.

## Tests

```bash
pytest -q
```
