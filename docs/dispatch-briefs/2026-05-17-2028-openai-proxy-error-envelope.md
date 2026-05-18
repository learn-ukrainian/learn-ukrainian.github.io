# Dispatch brief — #2028: OpenAI proxy 422 validation errors must use OpenAI error envelope

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952, enforced by `delegate.py dispatch`)
**Closes:** #2028 (HIGH severity bug from Gemini-3.1-pro adversarial review of PR #2025)

---

## Why

Per issue #2028: when a request fails Pydantic validation (e.g. missing `messages` array), the OpenAI proxy at `scripts/ai_agent_bridge/openai_proxy.py` currently returns FastAPI's default 422 envelope (`{"detail":[{"loc":["body","messages"],"msg":"..."}]}`). Strict OpenAI API clients (litellm, OpenWebUI) expect every error to use the OpenAI spec (`{"error":{"message":"...","type":"...","code":"..."}}`) and will crash on the FastAPI-native shape.

Current test `test_chat_completions_missing_messages_returns_422` in `tests/ai_agent_bridge/test_openai_proxy.py` LOCKS IN the wrong behavior — it must be flipped to assert the OpenAI envelope.

---

## What you build

Concrete fix template from the issue body (use as starting point, refine for our actual exception envelope helper):

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    first = exc.errors()[0] if exc.errors() else {}
    msg = first.get("msg", "validation error")
    loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
    return JSONResponse(
        status_code=422,
        content={"error": {
            "message": f"{msg} ({loc})" if loc else msg,
            "type": "invalid_request_error",
            "code": "validation_error",
        }},
    )
```

Look at the existing `_openai_error` helper in `openai_proxy.py` (if present) and route the handler through that for consistency rather than constructing the dict inline.

### Files to change

| File | Action |
|---|---|
| `scripts/ai_agent_bridge/openai_proxy.py` | Add `RequestValidationError` handler that returns OpenAI envelope |
| `tests/ai_agent_bridge/test_openai_proxy.py` | Flip `test_chat_completions_missing_messages_returns_422` to assert `error` envelope. Add 2-3 more cases: missing model, invalid JSON body, wrong field type |

### Tests to write

Mandatory cases on top of the flipped existing test:

1. **Missing `messages` → OpenAI envelope shape**: assert response is `{"error": {"message": ..., "type": "invalid_request_error", "code": "validation_error"}}` and `loc` info is in `message`.
2. **Missing `model`**: same envelope shape, includes "model" in message.
3. **`messages` wrong type** (string instead of list): same envelope.
4. **Empty body** (`{}`): same envelope, mentions the first missing required field.
5. **422 status code preserved**: each test asserts `response.status_code == 422`.

Reuse the existing test fixtures in `test_openai_proxy.py` — don't reinvent the test client.

---

## Verifiable claims this PR must produce (per #M-4)

| Claim | Tool + raw output to quote in PR body |
|---|---|
| Handler added | `git diff scripts/ai_agent_bridge/openai_proxy.py` showing the new `@app.exception_handler` block |
| Tests flipped + added | `git diff tests/ai_agent_bridge/test_openai_proxy.py` showing the renamed/flipped existing test + new 4 cases |
| Tests pass | `.venv/bin/pytest tests/ai_agent_bridge/test_openai_proxy.py -v` final summary line raw |
| Full bridge tests still green | `.venv/bin/pytest tests/ai_agent_bridge/ -q` final summary line raw (NO `-x` per #1942) |
| Ruff clean | `.venv/bin/ruff check scripts/ai_agent_bridge/openai_proxy.py tests/ai_agent_bridge/test_openai_proxy.py` raw output |
| Repro now returns OpenAI envelope | smoke: `./services.sh restart bridge 2>/dev/null; sleep 2; curl -sX POST http://127.0.0.1:8767/v1/chat/completions -H 'content-type: application/json' -d '{"model":"codex"}'` raw output should be `{"error":{"message":"...","type":"invalid_request_error","code":"validation_error"}}` (NOTE: if bridge restart from inside the worktree is awkward, mention in PR body and leave the smoke for the orchestrator) |
| Commit landed + PR opened | `git log -1 --oneline` raw + `gh pr view --json url` raw URL |

---

## Worktree setup

`delegate.py dispatch --worktree` handles creation. Branch name: `fix/openai-proxy-error-envelope-2028`.

---

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/ai_agent_bridge/test_openai_proxy.py -v
.venv/bin/pytest tests/ai_agent_bridge/ -q
.venv/bin/ruff check scripts/ai_agent_bridge/openai_proxy.py tests/ai_agent_bridge/test_openai_proxy.py
.venv/bin/python -m pre_commit run --files scripts/ai_agent_bridge/openai_proxy.py tests/ai_agent_bridge/test_openai_proxy.py
git diff --stat origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.

---

## Commit + PR

Title: `fix(bridge/proxy): 422 validation errors use OpenAI error envelope (#2028)`

Commit message:

```
fix(bridge/proxy): 422 validation errors use OpenAI error envelope (#2028)

FastAPI's default 422 response is `{"detail":[{"loc":[...],"msg":"..."}]}`
which violates the OpenAI API spec. Strict clients (litellm, OpenWebUI)
crash when parsing it because they expect the OpenAI error envelope:
`{"error":{"message":"...","type":"...","code":"..."}}`.

Adds RequestValidationError handler that catches Pydantic validation
errors and reshapes them into the OpenAI envelope, preserving status
422 and including the failing field location in the message.

Flipped test_chat_completions_missing_messages_returns_422 to assert
the new shape (it was locking in the wrong behavior). Added 4 more
validation cases: missing model, wrong messages type, empty body,
status-code preservation.

Found by Gemini-3.1-pro adversarial review of PR #2025
(audit/2026-05-16-openai-proxy-gemini-review/REPORT.md).
Closes #2028.

Verification:
* tests/ai_agent_bridge/test_openai_proxy.py: <quote pytest final line>
* full bridge tests: <quote pytest final line>
* ruff: <quote raw>
* curl repro returns OpenAI envelope: <quote stdout>
```

PR body:

```markdown
## Summary

Closes #2028. Adds a `RequestValidationError` handler to the OpenAI proxy at `scripts/ai_agent_bridge/openai_proxy.py` so 422 validation errors return the OpenAI error envelope instead of FastAPI's default `detail` array. Flips the existing test that was locking in the wrong behavior + adds 4 more validation cases.

## Verifiable claims (per #M-4)

* `git diff --stat`: <quote raw>
* `pytest test_openai_proxy.py`: <quote final line>
* `pytest tests/ai_agent_bridge/`: <quote final line>
* `ruff`: <quote raw>
* curl repro now returns OpenAI envelope: <quote stdout>

## Test plan

* [x] `test_chat_completions_missing_messages_returns_422` flipped to assert OpenAI envelope
* [x] New: missing `model` → OpenAI envelope
* [x] New: `messages` wrong type → OpenAI envelope
* [x] New: empty body `{}` → OpenAI envelope
* [x] New: status code 422 preserved across cases
* [x] Full `tests/ai_agent_bridge/` green
```

NO `--auto-merge`. Leave the PR open; orchestrator merges after CI green.

---

## Anti-fabrication preamble

If the proxy already has a custom `_openai_error` helper, route the new handler THROUGH it for consistency rather than constructing the envelope inline — quote the helper signature in the PR body to prove you found it.

If `test_chat_completions_missing_messages_returns_422` doesn't exist or has a different name, STOP and quote the actual test name; rename + flip rather than silently adding a duplicate.

If FastAPI's `RequestValidationError` is already handled in our codebase via a different mechanism (middleware, custom Pydantic config), prefer extending that existing path rather than adding a new exception_handler — quote the existing path in the PR body.
