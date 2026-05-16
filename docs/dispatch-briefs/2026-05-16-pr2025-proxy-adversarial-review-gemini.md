# Dispatch brief — Adversarial review of OpenAI-compat proxy (PR #2025, just merged)

> **Owner:** Gemini-3.1-pro (selected per kubedojo 2026-05-16 calibration:
> 2/2 #1229 bugs caught — strongest reviewer lane in the field)
> **Filed:** 2026-05-16
> **Mode:** read-only — NO code changes, NO commits, NO PRs.
> Output: a review report at `audit/2026-05-16-openai-proxy-gemini-review/REPORT.md`.

---

## What you're reviewing

PR #2025 just merged to main at commit `b9d5b36f2b`:

```
docs/best-practices/openai-compat-proxy.md |  20 ++
scripts/ai_agent_bridge/_cli.py            |  27 +++
scripts/ai_agent_bridge/openai_proxy.py    | 376 +++++++++++++++++++++++++++++
tests/ai_agent_bridge/test_openai_proxy.py | 211 ++++++++++++++++
4 files changed, 634 insertions(+)
```

Spec it implements: `docs/dispatch-briefs/2026-05-16-openai-compat-bridge-proxy-codex.md`.

It's a FastAPI service exposing 4 agent CLIs (Codex / Gemini / Claude headless /
Grok-via-Hermes) behind `POST /v1/chat/completions` + `GET /v1/models` +
`GET /healthz` on `127.0.0.1:8767`. Translates OpenAI request envelopes into
subprocess invocations of the underlying CLI per backend, returns OpenAI
response envelopes.

11 mocked tests pass. Live smoke tests against `/v1/models`, `/healthz`, and
the 404-unknown-model path all pass.

## What we want from you

**Adversarial review focused on these concrete attack surfaces** (not a
general code walk-through). Each finding should be specific enough to fix
or reproduce.

1. **Subprocess argv-injection surface.**
   - Read `_codex_backend`, `_gemini_backend`, `_claude_backend`,
     `_hermes_backend` (or whatever they're named in the implementation).
   - For each, trace how the user's `messages[].content` reaches the
     subprocess argv. Is it ever interpolated into a `shell=True` call? Is
     it passed as a single argv element via list form? Does the
     `model` parameter (which is checked against an allowlist before
     dispatch — confirm) get to argv safely?
   - Specific concern: a malicious request body with shell metachars
     (`; rm -rf`, `$(...)`, backticks) in `messages[0].content` — does it
     hit a shell at any layer?

2. **Message-flatten correctness across edge cases.**
   - `test_message_flatten_preserves_role_order` covers the happy path.
     What about: empty `messages: []` (should 422?), single `system`
     with no `user` (degenerate prompt; what does the backend get?), `system`
     in non-first position (OpenAI spec allows it; do we honor or reject?),
     consecutive `user` turns with no `assistant` between (legal in OpenAI;
     does the flatten produce a sensible prompt?), `assistant` turn before
     any `user` (degenerate; does it break?)
   - Look at the actual flatten implementation. Are there off-by-one bugs?
     Round-numbering inconsistencies? Missing role labels?

3. **Error envelope conformance.**
   - Read OpenAI's actual error response spec
     (`{"error":{"message","type","code","param"}}`) and check each error
     path returns a conforming envelope. The brief required: 404
     `model_not_found`, 502 `backend_failed`, 504 `backend_timeout`, 422
     missing-messages.
   - Specific concern: do error responses leak internal details (file
     paths, stack traces, secret-like strings) in `error.message`?
     Compare to OpenAI's actual error messages, which are short and
     don't expose backend internals.

4. **Race conditions in `_hermes_backend`.**
   - The Grok onboarding `grok_stage_runner.py` mutates
     `~/.hermes/config.yaml` per call (atomic backup-swap-restore).
     The brief explicitly forbade per-request mutation in the proxy
     because it's race-prone for a multi-tenant server. Verify the
     implementation respects this.
   - If `_hermes_backend` does write to that config, find the race
     window and propose a fix.

5. **Token accounting honesty.**
   - The brief required: return `0` when the backend doesn't surface
     real token counts; do NOT fabricate plausible numbers.
   - Read the `usage` field construction in each backend. Does any
     backend invent token counts (e.g. `len(prompt) // 4`)? If so, the
     fix is "return 0" — flag it.

6. **Backend timeout behavior.**
   - The brief specified default 120s per backend, configurable via env
     `BRIDGE_PROXY_BACKEND_TIMEOUT_S`. Verify the timeout is actually
     applied (i.e. `subprocess.run(..., timeout=...)`), not just
     declared. The 504 test mocks `subprocess.TimeoutExpired` but doesn't
     prove the live timeout fires.

7. **Localhost-only enforcement.**
   - The brief said localhost-only for v1. Is the host hardcoded to
     `127.0.0.1`? Or does `ab serve --openai --host 0.0.0.0` silently
     accept binding to all interfaces? If the latter, propose a guard
     (e.g. require an explicit `--allow-public` flag for non-localhost
     hosts).

8. **Healthz probe correctness.**
   - The `/healthz` endpoint probes each backend. What happens if a
     backend CLI is missing? Times out? Returns non-zero exit? Is the
     probe cached, or hammered on every healthcheck?
   - Specific concern: a 30s healthcheck cron polling /healthz could
     fork 4 CLI subprocesses per call if there's no cache.

9. **Test coverage gaps.**
   - The 11 tests were specified in the brief. Are there obvious
     coverage gaps that would let real bugs through? Empty-message-list,
     `assistant`-only conversation, very long content (10MB), Unicode
     edge cases (BOM, RTL marks, control chars), nested tool-call
     content (since OpenAI spec allows it but we don't translate it).

10. **General idiom / FastAPI usage.**
    - Are the Pydantic models defined with the right field constraints
      (e.g. `messages: list[Message] = Field(min_length=1)` to enforce
      non-empty)?
    - Is `app = FastAPI()` configured with a sensible `title`/
      `description`/`version` so OpenAPI docs render usefully?
    - Are there missing security headers we should set even on
      localhost (e.g. `X-Content-Type-Options: nosniff`)?

## What you should NOT do

- Do NOT propose new features (streaming, tool-use translation, auth,
  Assistants API). Those are explicitly Phase 2 deferred.
- Do NOT propose architectural rewrites. The Phase 1 surface is
  intentionally narrow.
- Do NOT mutate any code. Read-only.
- Do NOT open a PR or commit anything.

## Output format

Write your review to `audit/2026-05-16-openai-proxy-gemini-review/REPORT.md`.

Structure:

```markdown
# OpenAI-compat proxy adversarial review (Gemini-3.1-pro)

> Reviewing: PR #2025 merged at b9d5b36f2b
> Reviewer: gemini-3.1-pro-preview (selected per kubedojo 2026-05-16 calibration)
> Date: 2026-05-16

## Executive summary

(2-3 sentences: how many findings, severity distribution, overall verdict.)

## Findings

### [SEV] Finding 1 — <one-line title>

**Where:** `<file>:<line>` or `<file>:<function_name>`
**What:** What the bug or risk is, in concrete terms.
**Why it matters:** What goes wrong if it's exploited / triggered.
**Reproduction:** Specific input / command / call sequence to demonstrate.
**Suggested fix:** One sentence (or a code snippet if obvious).

(Repeat per finding, ordered by severity.)

## Coverage gaps (for Phase 2 follow-ups)

- ...

## What looks good

(Brief positive notes — keep this section short, only highlight what
you'd specifically want preserved through future refactors.)
```

Severity scale:
- **CRITICAL** — exploitable security or correctness bug; ship-blocker.
- **HIGH** — bug that affects normal usage paths.
- **MEDIUM** — edge-case bug or significant code-smell with real risk.
- **LOW** — nit, style, or hypothetical risk.

If you have ZERO findings of CRITICAL or HIGH severity, that's a clean
verdict — say so explicitly in the executive summary.

## Read-only commands you'll need

```bash
cat scripts/ai_agent_bridge/openai_proxy.py
cat tests/ai_agent_bridge/test_openai_proxy.py
cat scripts/ai_agent_bridge/_cli.py
cat docs/best-practices/openai-compat-proxy.md
cat docs/dispatch-briefs/2026-05-16-openai-compat-bridge-proxy-codex.md  # the spec
git log --oneline -1 b9d5b36f2b   # confirm SHA
```

You may also start the server in a sandbox to probe behavior:

```bash
.venv/bin/python -c "from scripts.ai_agent_bridge.openai_proxy import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8768, log_level='warning')" &
SERVER_PID=$!
sleep 2

# Probe whatever you suspect:
curl -s http://127.0.0.1:8768/v1/models
curl -s -X POST http://127.0.0.1:8768/v1/chat/completions -H 'content-type: application/json' -d '{"model":"codex","messages":[]}'  # empty messages — does it 422?
# ...

kill $SERVER_PID
```

## Acceptance

You're done when:
- [ ] `audit/2026-05-16-openai-proxy-gemini-review/REPORT.md` exists with the structure above
- [ ] Each finding has all 5 fields (Where / What / Why / Reproduction / Fix)
- [ ] At least 10 attack surfaces from the list above are addressed (either as findings OR as "checked, looks good")

The orchestrator will read your report after you finish, file follow-up
issues for HIGH/MEDIUM findings, and ship CRITICAL fixes immediately.

---

*Brief format: MD per #M-2 (ai → ai). Read-only mode means no commits, no
PRs, no file mutations outside the audit dir. Reviewer lane authority:
kubedojo 2026-05-16 calibration scoreboard (gemini-3.1-pro 2/2 #1229 bugs).*
