# Dispatch brief — Issue #2029: bridge /healthz TTL cache (DoS mitigation)

**Agent:** DeepSeek-pro hermes
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952)
**Issue:** #2029 — bridge/proxy `/healthz` forks 4 subprocesses per request
**Severity:** MEDIUM (DoS surface — external monitoring polling every 5s
forks 20 subprocesses/sec)

---

## Why

Every `GET /healthz` request synchronously runs 4 CLI `--version` probes
(codex, gemini, claude, hermes) with 1-second timeouts each. External
monitors polling /healthz at 5s intervals fork 4 processes/poll constantly;
an attacker can DoS the proxy by spamming /healthz; if one backend hangs,
the entire endpoint blocks for 1+ seconds.

## What you build

### 1. TTL cache for backend availability probes

In the bridge OpenAI proxy server (`scripts/ai_agent_bridge/openai_proxy/`
— locate the `/healthz` handler):

- Probe results cached for **60 seconds** (configurable via env var
  `BRIDGE_HEALTHZ_TTL_SECS`, default 60).
- Use a simple in-process dict `{backend_name: (timestamp, ok_bool, version_str)}`.
- On request: if `time.monotonic() - cached_timestamp < TTL`, return cached;
  else re-probe.
- **First-request behavior**: cold cache must NOT block all 4 probes
  serially. Run probes concurrently via `asyncio.gather` (the server is
  async FastAPI) OR via `ThreadPoolExecutor(max_workers=4)`. Pick whichever
  matches the existing handler shape — inspect first.
- The probe itself stays unchanged (1-second timeout per backend); only
  the cache wrapping is new.

### 2. Optional: background refresh task (only if trivial)

If FastAPI's lifespan/startup pattern is already in use in the server
module, add a background `asyncio.create_task(...)` that refreshes the
cache every TTL seconds. This makes /healthz return in <1ms always
(no per-request probing). **Skip if it requires meaningful refactoring**
— TTL-on-demand is sufficient for the DoS mitigation.

### 3. Tests

In `tests/ai_agent_bridge/test_openai_proxy_healthz.py` (or wherever
existing /healthz tests live — locate first):

1. **Cache hit**: probe once, advance fake clock 30s, probe again → only 1 set of subprocess calls (mock the probe to count invocations).
2. **Cache expiry**: probe once, advance fake clock 70s, probe again → 2 sets of subprocess calls.
3. **Concurrent first-request**: simulate 10 concurrent /healthz calls with cold cache → only 1 set of subprocess calls (single-flight; if implementation doesn't single-flight that's acceptable but assert ≤4 sets — 4 backends, max 1 per backend).
4. **TTL env var override**: set `BRIDGE_HEALTHZ_TTL_SECS=5` → cache expires at 5s.
5. **Backend failure does not block other backends**: simulate one probe hanging (returns 1s timeout) → other 3 still return their results; total handler latency ≤ ~1.05s (not 4s serial).

### 4. Docstring + module-doc updates

Document the TTL behavior in the handler docstring and reference issue #2029.

---

## Verifiable claims this PR must produce (per #M-4)

| Claim | Tool + raw output to quote in PR body |
|---|---|
| Handler updated | `git diff --stat origin/main` showing the proxy file row |
| New tests pass | `.venv/bin/pytest tests/ai_agent_bridge/test_openai_proxy_healthz.py -v` final summary line raw |
| Existing bridge tests still pass | `.venv/bin/pytest tests/ai_agent_bridge/ -q` final summary line raw |
| Ruff clean | `.venv/bin/ruff check scripts/ai_agent_bridge/openai_proxy/ tests/ai_agent_bridge/test_openai_proxy_healthz.py` raw |
| Pre-commit clean | `.venv/bin/python -m pre_commit run --files <changed files>` raw |
| Commit + PR | `git log -1 --oneline` + `gh pr view --json url` raw |
| Manual DoS validation | If `ab serve --openai` works in the worktree: `ab serve --openai &` → `for i in $(seq 1 20); do curl -s http://127.0.0.1:8767/healthz; done` raw output + a `ps` showing no spawned codex/gemini processes during the burst. Skip with a note if ab serve requires extra setup. |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

`delegate.py dispatch --worktree` handles worktree creation. Canonical:
`.worktrees/dispatch/deepseek/2029-healthz-ttl-<timestamp>/`. Branch:
`fix/2029-healthz-ttl-cache`.

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/ai_agent_bridge/test_openai_proxy_healthz.py -v
.venv/bin/pytest tests/ai_agent_bridge/ -q
.venv/bin/ruff check scripts/ai_agent_bridge/openai_proxy/ tests/ai_agent_bridge/
.venv/bin/python -m pre_commit run --files <changed files>
git diff --stat origin/main
```

## Commit + PR

Standard conventional commit + PR body with the verifiable-claims raw
outputs quoted. No `--auto-merge`.

## Out of scope

- Don't refactor unrelated bridge code.
- Don't add metrics/prometheus endpoints (separate concern).
- Don't change probe content (versions still come from `--version` calls).
- Don't introduce a new config file just for `BRIDGE_HEALTHZ_TTL_SECS` —
  env var is sufficient.

## Anti-fabrication

Inspect the actual `/healthz` handler BEFORE writing tests — the file
layout may differ slightly from this brief. Quote the file path you
found in the PR body. If the handler doesn't actually fork 4
subprocesses (e.g. it already caches partially), STOP and quote what
you observed before proceeding — the issue may be already mitigated.
