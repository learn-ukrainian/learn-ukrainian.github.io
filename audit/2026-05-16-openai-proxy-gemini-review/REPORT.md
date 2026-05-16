# OpenAI-compat proxy adversarial review (Gemini-3.1-pro)

> Reviewing: PR #2025 merged at b9d5b36f2b
> Reviewer: gemini-3.1-pro-preview (selected per kubedojo 2026-05-16 calibration)
> Date: 2026-05-16

## Executive summary

I found 2 HIGH severity bugs and 2 MEDIUM/LOW severity issues. The most critical issue is a severe OS-level argument length limit vulnerability (`ARG_MAX` / `E2BIG`) caused by passing prompts via command-line arguments instead of `stdin` in 3 out of 4 backends. The other high-severity issue involves a spec violation in FastAPI's error handling for 422 validations. The Hermes race condition, token fabrication rules, and timeout specs were all correctly implemented per the dispatch brief.

## Findings

### [HIGH] Subprocess `ARG_MAX` vulnerability via argv injection

**Where:** `scripts/ai_agent_bridge/openai_proxy.py:_gemini_backend`, `_claude_backend`, `_hermes_backend`
**What:** The flattened prompt is passed to the underlying CLIs directly via command-line arguments (`argv`). For example, `f"--prompt={prompt}"` for Gemini and `--oneshot={prompt}` for Hermes.
**Why it matters:** While safe from shell injection (since `shell=False`), this is highly vulnerable to `OSError: [Errno 7] Argument list too long` (`E2BIG`). The OpenAI API commonly handles prompts exceeding 100K tokens. Passing a 300KB string via `argv` will immediately crash the backend subprocess on macOS (limit ~256KB) and most Linux distributions.
**Reproduction:** Send a `POST /v1/chat/completions` request to `gemini-3.0-flash-preview` where `messages[0].content` contains 300,000 characters. The proxy will return a 502 as the subprocess fails to spawn.
**Suggested fix:** Refactor all backends to pass the prompt via `stdin` (using the `input=prompt` parameter of `subprocess.run` which is already supported by `_run_backend_command`), exactly as it is safely handled in the `_codex_backend`.

### [HIGH] FastAPI 422 validation errors violate OpenAI error envelope spec

**Where:** `scripts/ai_agent_bridge/openai_proxy.py` (App-wide)
**What:** When a request fails Pydantic validation (e.g., missing the `messages` array), FastAPI automatically returns a 422 response with its default schema: `{"detail": [{"loc": ["body", "messages"], ...}]}`.
**Why it matters:** Strict OpenAI API clients expect all errors to follow the `{"error": {"message": "...", "type": "...", "code": "..."}}` shape. Returning FastAPI's native `detail` array will cause external clients to crash during error parsing. This incorrect behavior is currently enshrined in `test_chat_completions_missing_messages_returns_422`.
**Reproduction:** `curl -X POST http://127.0.0.1:8767/v1/chat/completions -H 'Content-Type: application/json' -d '{"model": "codex"}'`
**Suggested fix:** Add a custom `@app.exception_handler(RequestValidationError)` to catch Pydantic errors and format them into the proxy's `_openai_error` envelope. Update the associated test.

### [MEDIUM] `/healthz` endpoint forks 4 subprocesses synchronously on every request

**Where:** `scripts/ai_agent_bridge/openai_proxy.py:healthz`
**What:** Every GET to `/healthz` sequentially executes four CLI subprocesses (`codex --version`, `gemini --version`, etc.) with a 1-second timeout each.
**Why it matters:** An external load balancer or monitoring system polling this endpoint every 5 seconds will constantly fork processes on the host. An attacker (or aggressive monitoring) can trivially DoS the proxy by spamming `/healthz`. If one backend hangs, the health check takes >1s to respond, creating a bottleneck.
**Reproduction:** Run `ab serve --openai` and spam `curl http://127.0.0.1:8767/healthz` 100 times in parallel. Observe significant CPU usage spikes and response latency.
**Suggested fix:** Cache the probe results globally with a TTL (e.g., 30-60 seconds) using a background task, or remove the subprocess execution entirely and just return `{"ok": True}`.

### [LOW] Missing strict localhost bind enforcement

**Where:** `scripts/ai_agent_bridge/_cli.py` (`serve_parser.add_argument("--host")`)
**What:** The CLI accepts an arbitrary `--host` argument, allowing `ab serve --openai --host 0.0.0.0` to bind to all interfaces.
**Why it matters:** The dispatch brief explicitly specified "Localhost-only for v1." While the default is correct (`127.0.0.1`), allowing easy overrides without authentication risks accidental public exposure of the agent fleet.
**Reproduction:** `ab serve --openai --host 0.0.0.0`
**Suggested fix:** Add a strict check in `__main__.py` or `_cli.py` that rejects `--host` values other than `127.0.0.1` unless an `--allow-remote` flag is explicitly provided.

## Coverage gaps (for Phase 2 follow-ups)

- **Mocking at the wrong boundary:** The tests mock the backend callables (`_codex_backend`, etc.) rather than `_run_backend_command`. As a result, the `argv` construction logic is entirely untested. If a backend has a typo like passing `--prompt` instead of `--prompt=`, the tests would still pass.
- **Multimodal inputs:** The `Message` schema parsing (`_message_content_to_text`) correctly ignores complex objects like Anthropic's image blocks, but silently drops them. This is fine for Phase 1 but should be tracked for Phase 2.

## What looks good

- **Hermes Race Condition Avoided:** The `_hermes_backend` properly invokes `hermes` without dynamically altering `~/.hermes/config.yaml`, perfectly adhering to the dispatch brief's warning about multi-tenant race conditions.
- **Token Accounting Honesty:** The proxy strictly returns `0` for all token counts rather than fabricating heuristics, adhering to the brief's `#M-4` mandate.
- **Robust Exception Handling in Subprocesses:** The use of `_first_error_line` correctly extracts the first line of stderr, safely handling both `bytes` and `str` without throwing `UnicodeDecodeError`s even if the subprocess emits garbage characters.