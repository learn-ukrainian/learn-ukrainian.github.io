# OpenAI-Compatible Agent Proxy

`ab serve --openai` starts a localhost-only FastAPI service on
`127.0.0.1:8767` by default. It exposes:

- `GET /v1/models`
- `POST /v1/chat/completions`
- `GET /healthz`

The model registry lives in `scripts/ai_agent_bridge/openai_proxy.py` as
`_ROUTABLE_MODELS`. Add or remove routable public model IDs there first; the
models endpoint reads from that single source of truth.

Phase 1 is intentionally non-streaming and does not translate tool-use or
Assistants API envelopes. Token usage is reported as zero unless a backend
surfaces real counts; do not invent approximate totals in the response.

The Grok route uses `hermes -z PROMPT -m grok-4.3` and respects the user's
existing `~/.hermes/config.yaml`. The proxy must not mutate Hermes config per
request because that would be race-prone under concurrent clients.
