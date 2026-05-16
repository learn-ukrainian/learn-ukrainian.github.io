# Dispatch brief — OpenAI-compatible HTTP proxy for the agent fleet

> **Owner:** Codex
> **Filed:** 2026-05-16
> **Scope:** Add a new HTTP service that exposes our agent fleet (Codex /
> Gemini / Claude headless / Grok-via-Hermes) behind the OpenAI
> chat-completions API surface, so any OpenAI-compatible client can
> drive our agents without bespoke shims.

---

## Why this matters

Today every consumer that wants to call a non-Anthropic agent writes a
bespoke subprocess wrapper (`subprocess.run(["codex", "exec", ...])`,
`subprocess.run(["gemini", "-p", ...])`, `hermes -z PROMPT -m grok-4.3`).
Three concrete pains this proxy solves:

1. **Hermes / Grok 4.3 OAuth-403 inversion** — direct
   `api.x.ai/v1/chat/completions` calls return 403 (the OAuth token from
   `hermes auth add xai-oauth` carries session scope only). Today the
   integration path is `hermes -z` subprocess, which is fine for one-shot
   queries but doesn't compose with anything that expects a real HTTP
   `/v1/chat/completions`. The proxy lets external clients hit
   `http://127.0.0.1:8767/v1/chat/completions` with `model: "grok-4.3"`
   and we translate to `hermes -z` server-side. Closes the Grok onboarding
   gap from the 2026-05-16 handoff.
2. **One subprocess wrapper per agent rot** — `ab ask-codex`,
   `ab ask-gemini`, `ab ask-grok` each carries its own argv schema +
   warm-cache adapter + error parsing. The proxy thin-wraps the
   existing per-agent modules behind a single uniform HTTP surface.
3. **External OpenAI-compatible tools come along for free** —
   OpenWebUI, Continue.dev, Cursor sidecars, litellm, aider, sgpt — all
   speak OpenAI out of the box. Once the proxy exists, plugging any of
   them into our fleet is zero shim code per tool.

This is **NOT** a replacement for `delegate.py` (which orchestrates
worktree + commit + push + PR for autonomous code work) or for
`ab channel`/`ab discuss` (which manages multi-participant persistent
threads). Three concerns, three surfaces. Keep them separate.

---

## #M-4 deterministic-evidence preamble

The dispatch will produce verifiable claims. Each claim must be backed
by a concrete tool invocation in the PR body or commit message, with
raw output quoted (not paraphrased):

| Claim | Deterministic tool / output |
|---|---|
| "Server starts on :8767" | `curl -s http://127.0.0.1:8767/v1/models \| jq '.data[].id'` raw output |
| "Codex backend works" | `curl -s -X POST http://127.0.0.1:8767/v1/chat/completions -H 'content-type: application/json' -d '{"model":"codex","messages":[{"role":"user","content":"Reply with exactly the word: PONG"}]}' \| jq -r '.choices[0].message.content'` showing `PONG` |
| "Grok backend works" | Same curl with `"model":"grok-4.3"`, raw response showing a non-empty assistant message |
| "Gemini backend works" | Same curl with `"model":"gemini-3.0-flash-preview"` (or whatever model id the bridge currently routes to), raw response |
| "Claude backend works" | Same curl with `"model":"claude-opus-4-7"` or `"model":"claude-sonnet-4-7"`, raw response |
| "Tests pass" | `.venv/bin/python -m pytest tests/ai_agent_bridge/test_openai_proxy.py -v` final summary line raw |
| "Ruff clean" | `.venv/bin/ruff check scripts/ai_agent_bridge/openai_proxy.py tests/ai_agent_bridge/test_openai_proxy.py` raw output (`All checks passed!` or zero-error count) |
| "Commit landed" | `git log -1 --oneline` raw |
| "PR opened" | `gh pr view --json url -q '.url'` raw URL |

**No "I tested it" without a quoted command + cwd + raw output.**
Fabrication-resistant per `docs/best-practices/deterministic-over-hallucination.md`.

---

## Numbered steps (MANDATORY, no skipping)

### 1. Worktree setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b feat/openai-compat-bridge-proxy \
    .worktrees/dispatch/codex/openai-compat-proxy-2026-05-16 \
    origin/main
cd .worktrees/dispatch/codex/openai-compat-proxy-2026-05-16
```

All subsequent steps run from inside the worktree.

### 2. Implementation — `scripts/ai_agent_bridge/openai_proxy.py`

Single new module, FastAPI-based, entry point exposed via the existing
`ab` CLI as `ab serve --openai [--port PORT] [--host HOST]`. Default
port `8767`, default host `127.0.0.1`.

**Endpoints (Phase 1, narrow):**

- `GET /v1/models` — returns `{"object":"list","data":[{"id":"<model_id>","object":"model","created":<int>,"owned_by":"<family>"}, …]}` enumerating every routable model. Source of truth: a single `_ROUTABLE_MODELS` dict in `openai_proxy.py` of the form:
  ```python
  _ROUTABLE_MODELS: dict[str, ModelRoute] = {
      "codex": ModelRoute(family="openai-codex", backend=_codex_backend),
      "gemini-3.0-flash-preview": ModelRoute(family="google-gemini", backend=_gemini_backend),
      "gemini-3.1-pro-preview": ModelRoute(family="google-gemini", backend=_gemini_backend),
      "claude-opus-4-7": ModelRoute(family="anthropic", backend=_claude_backend),
      "claude-sonnet-4-7": ModelRoute(family="anthropic", backend=_claude_backend),
      "grok-4.3": ModelRoute(family="xai", backend=_hermes_backend),
  }
  ```
  Each backend is a callable taking `(model: str, messages: list[Message], **kwargs) -> CompletionResponse`.
- `POST /v1/chat/completions` — accepts the OpenAI request envelope, validates `model` against `_ROUTABLE_MODELS`, dispatches to the backend, returns OpenAI response envelope.
- `GET /healthz` — `{"ok": true, "backends": {"codex": true|false, …}}` with a 1-second probe per backend (try `<cli> --version` or equivalent cheap call). Used by external monitoring.

**Backend implementations** (one inner function per family, each ~30-50 LOC):

- `_codex_backend(model, messages, **kwargs)` — flatten messages to a single prompt (system → first system block; user/assistant rounds → `\n\n--- Round N ---\n[role]: content` concatenation), invoke `codex exec --json` (or whatever the headless flag is — verify with `codex exec --help` first), parse the final assistant message from JSON output. Reuse logic from `scripts/ai_agent_bridge/_codex.py` if a comparable helper exists.
- `_gemini_backend(model, messages, **kwargs)` — same flatten pattern, invoke `gemini -p PROMPT --model <model_id>`. Honor the bridge's existing Tier-2 warm-cache pattern (per `_gemini.py`); pass `--resume <session_uuid>` when a per-(client, conversation) session id is supplied via the OpenAI request's optional `user` field. v1: stateless OK; warm-cache is a v1.5 follow-up if it adds complexity.
- `_claude_backend(model, messages, **kwargs)` — flatten + invoke `claude -p PROMPT --bare --model <model_id>`. Reuse logic from `_claude.py` if present.
- `_hermes_backend(model, messages, **kwargs)` — flatten + invoke `hermes -z PROMPT -m <model_id>`. The 2026-05-16 handoff documents the exact subprocess pattern: `~/.hermes/config.yaml` controls `agent.reasoning_effort` (default `medium`, recommended for production per the calibration sweep in `audit/2026-05-15-grok-4.3-judge-calibration-with-mcp/`). v1: respect `~/.hermes/config.yaml` defaults; do NOT mutate config per-request (the calibration runner does that with atomic backup-swap-restore but it's race-prone for a multi-tenant proxy).

**Response envelope shape (OpenAI v1):**

```json
{
  "id": "chatcmpl-<uuid4>",
  "object": "chat.completion",
  "created": <unix_seconds>,
  "model": "<requested_model_id>",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "<backend output>"},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": <approx_or_zero>,
    "completion_tokens": <approx_or_zero>,
    "total_tokens": <approx_or_zero>
  }
}
```

**Token accounting:** Codex/Gemini/Claude/Hermes each report tokens
differently. v1: report `0` for all three when the backend doesn't
surface them in stdout, OR a heuristic char-count / 4 if you want a
rough number. **DO NOT fabricate plausible-looking token numbers.** If
you can't get a real count from the backend, return `0` and document the
gap in a TODO comment.

**Error handling:**

- Unknown `model` → HTTP 404 with OpenAI error envelope
  `{"error":{"message":"model '<id>' not found","type":"invalid_request_error","code":"model_not_found"}}`.
- Backend subprocess failure → HTTP 502 with
  `{"error":{"message":"<backend> backend failed: <stderr first line>","type":"upstream_error","code":"backend_failed"}}`.
- Subprocess timeout (default 120s per backend, configurable via env
  `BRIDGE_PROXY_BACKEND_TIMEOUT_S`) → HTTP 504 with timeout envelope.
- Invalid request body (missing `messages`, malformed `model`, etc.) →
  HTTP 422 with field-level error.

**Out-of-scope for v1 (file as follow-up issues if you want to track them):**

- Streaming responses (SSE). Most OpenAI clients want it; can add when
  a concrete UI client demands it. Document the gap in the README.
- Tool-use translation. OpenAI vs Anthropic vs Codex tool envelope
  schemas are non-trivial; add when a concrete pipeline needs it.
- The OpenAI Assistants API (`/v1/threads`, `/v1/threads/{id}/runs`).
  Maps to our channels/discuss but no external client wants it today.
- Auth. Localhost-only `127.0.0.1` for v1. Add a token gate when we
  expose beyond localhost.
- Per-request cost telemetry (push to Monitor API
  `/api/state/routing-budget`). Hook in once basic surface is stable.

### 3. CLI integration — `scripts/ai_agent_bridge/__main__.py`

Add a new subcommand:

```
ab serve --openai [--port 8767] [--host 127.0.0.1]
```

Implementation: import the FastAPI app from `openai_proxy.py`,
`uvicorn.run(app, host=host, port=port, log_level="info")`. Wire into
the existing argparse subcommand registry.

If `ab` already has a `serve` subcommand, add `--openai` as a sub-mode
flag rather than duplicating. Verify by running `ab --help` first and
reading the existing structure.

### 4. Tests — `tests/ai_agent_bridge/test_openai_proxy.py`

Use FastAPI's `TestClient` — DO NOT spin up a real subprocess in
tests. Mock each backend with `monkeypatch` to return a deterministic
canned response.

**Required test cases (each must pass independently):**

1. `test_models_endpoint_lists_routable_models` — `GET /v1/models`
   returns 200 + every `_ROUTABLE_MODELS` key in `data[].id`.
2. `test_chat_completions_codex_round_trip` — mock `_codex_backend`
   to return `"hello from codex"`; assert response envelope has the
   right `model`, `choices[0].message.content == "hello from codex"`,
   `finish_reason == "stop"`.
3. `test_chat_completions_grok_via_hermes` — same shape against
   `_hermes_backend` mock; assert `model: "grok-4.3"` round-trips.
4. `test_chat_completions_gemini_round_trip` — same against
   `_gemini_backend`.
5. `test_chat_completions_claude_round_trip` — same against
   `_claude_backend`.
6. `test_chat_completions_unknown_model_returns_404` — assert HTTP
   404 + OpenAI error envelope shape (`error.code == "model_not_found"`).
7. `test_chat_completions_backend_failure_returns_502` — mock backend
   to raise `subprocess.CalledProcessError`; assert HTTP 502 +
   `error.code == "backend_failed"` + first line of stderr in
   `error.message`.
8. `test_chat_completions_backend_timeout_returns_504` — mock backend
   to raise `subprocess.TimeoutExpired`; assert HTTP 504 +
   `error.code == "backend_timeout"`.
9. `test_chat_completions_missing_messages_returns_422` — POST with
   `{"model":"codex"}` (no `messages`); assert HTTP 422 + field error.
10. `test_message_flatten_preserves_role_order` — backend receives
    flattened prompt with `system` first, then alternating `user` /
    `assistant`; assert via mock that the `prompt` argument the
    backend was called with includes all three roles in order.
11. `test_healthz_endpoint_returns_backend_status` — mock each backend
    `_probe()` to return True/False; assert `/healthz` JSON shape.

**Coverage target: every backend dispatch path + every error class +
the model registry.**

### 5. Lint

```bash
.venv/bin/ruff check scripts/ai_agent_bridge/openai_proxy.py \
    tests/ai_agent_bridge/test_openai_proxy.py \
    scripts/ai_agent_bridge/__main__.py
.venv/bin/ruff format --check scripts/ai_agent_bridge/openai_proxy.py \
    tests/ai_agent_bridge/test_openai_proxy.py
```

Quote raw output in the PR body.

### 6. Pytest (full bridge subtree, not just the new file)

```bash
.venv/bin/python -m pytest tests/ai_agent_bridge/ -v
```

Two reasons not just the new test file: (a) ensures `ab` CLI changes
didn't break sibling subcommands, (b) #M-7 — the deploy/tests
invariant. Quote the final summary line.

### 7. Smoke test against real backends (LIVE, not mocked)

Once tests pass, start the proxy and round-trip a real call against
each backend (where the CLI is installed and authenticated). Quote
each curl + raw JSON response in the PR body.

```bash
.venv/bin/python -c "from scripts.ai_agent_bridge.openai_proxy import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8767)" &
SERVER_PID=$!
sleep 2

curl -s http://127.0.0.1:8767/v1/models | jq

# Codex round-trip
curl -s -X POST http://127.0.0.1:8767/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{"model":"codex","messages":[{"role":"user","content":"Reply with exactly: PONG"}]}' \
    | jq -r '.choices[0].message.content'

# Grok round-trip via Hermes
curl -s -X POST http://127.0.0.1:8767/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{"model":"grok-4.3","messages":[{"role":"user","content":"What is 2+2? Answer with just the number."}]}' \
    | jq -r '.choices[0].message.content'

# Gemini round-trip
curl -s -X POST http://127.0.0.1:8767/v1/chat/completions \
    -H 'content-type: application/json' \
    -d '{"model":"gemini-3.0-flash-preview","messages":[{"role":"user","content":"Reply with exactly: PONG"}]}' \
    | jq -r '.choices[0].message.content'

kill $SERVER_PID
```

If any backend fails the live round-trip, file a follow-up issue;
don't block the PR on it (e.g. if Hermes isn't installed in your
worktree's PATH, document and skip — the test mock covers correctness;
live coverage is supplementary).

### 8. Commit

```bash
git add scripts/ai_agent_bridge/openai_proxy.py \
        scripts/ai_agent_bridge/__main__.py \
        tests/ai_agent_bridge/test_openai_proxy.py \
        docs/best-practices/openai-compat-proxy.md  # README/docs if you ship one
git commit -m "$(cat <<'EOF'
feat(bridge): OpenAI-compatible HTTP proxy at :8767

Adds scripts/ai_agent_bridge/openai_proxy.py — FastAPI service exposing
the agent fleet (Codex / Gemini / Claude headless / Grok-via-Hermes)
behind /v1/chat/completions and /v1/models, plus /healthz.

Why: every consumer that wants a non-Anthropic agent today writes a
bespoke subprocess wrapper. This proxy thin-wraps the existing per-agent
modules behind a single uniform HTTP surface, so any OpenAI-compatible
client (OpenWebUI, Continue.dev, litellm, aider) drives our fleet with
zero shim code per tool. Also closes the Grok 4.3 OAuth-403 inversion
gap from the 2026-05-16 handoff: Hermes can now call us at
:8767/v1/chat/completions instead of us calling Hermes via -z.

Phase 1 scope (narrow, per dispatch brief):
- /v1/chat/completions, /v1/models, /healthz
- Backends: codex, gemini, claude, grok-via-hermes
- Localhost-only, no auth, no streaming, no tool-use translation
- Token accounting reports 0 when backend doesn't expose it (no fabrication)

Out of scope (deferred until concrete client demand):
- SSE streaming
- Tool-use translation (OpenAI<->Anthropic<->Codex schemas)
- Assistants API (/v1/threads)
- Auth / token gate

Ships as a third surface alongside Monitor API (:8765, state queries)
and ab CLI (channels/discuss). Three concerns, three surfaces.

Test plan: 11 mocked TestClient cases + 4 live curl round-trips per
backend (raw output in PR body).

Co-Authored-By: Codex (gpt-5.5)
EOF
)"
```

### 9. Push

```bash
git push -u origin feat/openai-compat-bridge-proxy
```

### 10. Open PR — DO NOT auto-merge

```bash
gh pr create --title "feat(bridge): OpenAI-compatible HTTP proxy at :8767" --body "$(cat <<'EOF'
## Summary

Adds an OpenAI-compatible HTTP proxy at `:8767` that wraps Codex,
Gemini, Claude headless, and Grok-via-Hermes behind
`/v1/chat/completions` + `/v1/models` + `/healthz`.

Phase 1 is narrow per the dispatch brief
(`docs/dispatch-briefs/2026-05-16-openai-compat-bridge-proxy-codex.md`):
- 4 backends, 11 mocked tests, 4 live curl round-trips
- No streaming, no tool-use translation, no auth — all deferred
- Localhost-only

Closes the Grok OAuth-403 inversion + sets up any future
OpenAI-compatible client (OpenWebUI, Continue.dev, etc.) for
zero-shim integration.

## Test plan

- [x] `pytest tests/ai_agent_bridge/test_openai_proxy.py` (paste raw summary line)
- [x] `pytest tests/ai_agent_bridge/` (full bridge subtree — paste raw summary)
- [x] `ruff check` clean (paste raw output)
- [x] Live curl: `/v1/models` (paste raw JSON)
- [x] Live curl: codex round-trip (paste raw response)
- [x] Live curl: grok round-trip via Hermes (paste raw response)
- [x] Live curl: gemini round-trip (paste raw response)
- [x] Live curl: claude round-trip (paste raw response — skip if claude headless not in worktree PATH; document)

## Verifiable evidence

(Codex must paste raw command + cwd + output here for each claim above.)

🤖 Generated with [Codex](https://codex.openai.com)
EOF
)"
```

**No `--admin`, no auto-merge.** Orchestrator will review.

---

## Acceptance criteria

PR is ready for review when ALL of the following are satisfied with
quoted evidence in the PR body:

- [ ] `pytest tests/ai_agent_bridge/test_openai_proxy.py` → all 11 tests pass
- [ ] `pytest tests/ai_agent_bridge/` → full bridge subtree green (no regression)
- [ ] `ruff check` → clean (or zero-error count)
- [ ] `curl /v1/models` → returns ≥4 models
- [ ] `curl /v1/chat/completions {model:"codex"}` → 200 with non-empty assistant message
- [ ] `curl /v1/chat/completions {model:"grok-4.3"}` → 200 with non-empty assistant message
- [ ] `curl /v1/chat/completions {model:"gemini-3.0-flash-preview"}` → 200 with non-empty assistant message
- [ ] `curl /v1/chat/completions {model:"unknown-model-xyz"}` → 404 with OpenAI error envelope
- [ ] PR body contains raw command + cwd + output for each backend (no paraphrasing)

If any backend's live round-trip can't run in the worktree (missing
CLI, missing auth), document the gap inline in the PR body and file a
follow-up issue; do NOT block the PR on it. The mocked test suite
covers correctness; live coverage is supplementary signal.

---

## Failure modes to avoid

- **Don't fabricate token counts.** Return `0` when the backend doesn't
  surface them. The orchestrator will grep the PR body for suspicious
  round-number token totals.
- **Don't reinvent the model registry.** Source of truth is the
  `_ROUTABLE_MODELS` dict in `openai_proxy.py`. If you find yourself
  hardcoding model lists in three places, refactor to one source.
- **Don't auto-merge.** Even if all CI is green, leave the PR open.
- **Don't widen scope.** No streaming, no tool-use, no Assistants API,
  no auth in this PR. Each is its own follow-up issue.
- **Don't skip the live round-trips.** The mocks prove the wiring
  compiles; the live curls prove the subprocess calls actually work
  end-to-end. Both layers are required evidence.

---

## After PR opens — orchestrator (Claude) will

1. Read the PR diff + verify quoted evidence matches reality
   (re-run a sample of the curl commands).
2. If green: merge with `--squash --delete-branch` (no `--admin`).
3. If REVISE: post review comments and dispatch revision.
4. Then dispatch Codex (independent run) for adversarial review of the
   merged code. Reviewer focuses on: subprocess argv-injection
   surface, message-flatten correctness across edge cases (empty
   `messages`, single `system`, role-order violations), error envelope
   conformance to OpenAI spec, race conditions in `_hermes_backend` if
   it touches `~/.hermes/config.yaml`.
5. File follow-up issues for the Phase 2 deferred items
   (streaming, tool-use, Assistants API, auth, token telemetry,
   delegate.py Grok dispatch route) so they don't get lost.

---

*Brief format: MD per #M-2 (ai → ai). Authority for the dispatch
checklist: MEMORY DISPATCH-BRIEF CHECKLIST + #M-4 deterministic-evidence
preamble. Companion: `docs/best-practices/deterministic-over-hallucination.md`.*
