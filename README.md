# Manolo AI Helper

FastAPI assistant with orchestrator loop, pluggable LLM providers (OpenAI, llama.cpp via llama-server), SQLite storage, and a minimal streaming chat UI.

## Setup

```bash
uv sync
cp .env.example .env
# Edit .env: OPENAI_API_KEY or point LLAMA_CPP_BASE_URL at llama-server
```

## Run

```bash
uv run poe main
# or: uv run python -m manolo
```

Open http://127.0.0.1:8000 for the chat UI.

## llama.cpp

Start [llama-server](https://github.com/ggerganov/llama.cpp) with an OpenAI-compatible API, then set:

```env
LLM_PROVIDER=llama_cpp
LLAMA_CPP_BASE_URL=http://127.0.0.1:<port>/v1
```

## Tests (optional)

```bash
uv run poe test
# with coverage report: uv run poe test_cov
```

## License

MIT
