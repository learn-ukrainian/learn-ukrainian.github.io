# Dispatch: fix cursor + grok-build so both work as wiki reviewers (#3087 bakeoff, #3151)

Goal: make BOTH `cursor` and `grok-build` produce a valid dimensional-review verdict
through `scripts/wiki/review.py`, so the #3087 reviewer bakeoff can include them. Two
independent root causes, both diagnosed + (grok) verified by the orchestrator.

## A. grok-build — invalid model id (VERIFIED fix)
Native `grok` CLI models (`grok models`): **`grok-build`** (default) and `grok-composer-2.5-fast`.
There is **no `grok-4.20`** — that is a *Hermes* model id (used by the separate `grok` agent).
The grok-build adapter/registry wrongly default to `grok-4.20`, so every invoke dies with
`Couldn't set model 'grok-4.20': unknown model id`.

VERIFIED working: `grok --prompt-file <f> --model grok-build --output-format json` → `{"text":"PONG",...}` exit 0.

Fix — change `grok-4.20` → `grok-build` in exactly these 3 spots (leave the *comments* that
correctly describe Hermes grok-4.3/grok-4.20, and leave `linear_pipeline.py:138` cursor-tools alone):
1. `scripts/agent_runtime/registry.py:123` — grok-build `"default_model": "grok-4.20"` → `"grok-build"`
2. `scripts/agent_runtime/adapters/grok_build.py:50` — `GROK_BUILD_DEFAULT_MODEL = os.environ.get("LEARN_UK_GROK_BUILD_MODEL", "grok-4.20")` → default `"grok-build"`
3. `scripts/ai_agent_bridge/_model.py:8` — `GROK_BUILD_DEFAULT_MODEL = "grok-4.20"` → `"grok-build"`
Closes #3151.

## B. cursor — sources MCP never wired (primary hypothesis, CONFIRM then fix)
`scripts/wiki/review.py::_tool_config_for` builds `tool_config` with `mcp_servers=["sources"]`
(via `build_mcp_tool_config`). The Hermes adapters consume this (`hermes_deepseek.py` has
`_sources_mcp_registered` + `_translate_mcp_prefix_for_hermes`) so deepseek/grok/qwen reviewers
get the `sources` MCP. **`CursorAdapter` ignores `mcp_servers` entirely** — it only reads
`cursor_workspace`/`approve_mcps`/`cursor_mode`/`sandbox`. So cursor-agent has NO `sources` server,
the review's `mcp__sources__*` tool calls can't resolve, and the invoke returns `ok=False`
(captured: only `init`+`user` events, no assistant/result). cursor-agent itself is healthy —
`echo "Reply PONG" | cursor-agent -p --model auto --output-format stream-json --trust` returns
`result:"PONG"` exit 0.

Steps:
1. **Confirm** the cause: run one cursor review (repro below) with full stdout+exit capture; verify
   the failure is the missing `sources` MCP (cursor can't call `mcp__sources__*`), not the
   ok/parse logic and not the secondary stale-session resume (the run reused a foreign
   session id `7f081f7f…` — `_find_session_id_on_disk` may auto-resume an unrelated session; fix
   that too if it interferes — a fresh review must NOT resume an unrelated session).
2. **Wire the sources MCP for cursor-agent.** cursor uses an `mcp.json` (`~/.cursor/mcp.json` or a
   passed config) + `--approve-mcps`. When `tool_config["mcp_servers"]` includes `sources`, the
   adapter must register the local `sources` HTTP MCP (port 8766) for the cursor subprocess
   (project/temp `.cursor/mcp.json` or the documented cursor MCP-config flag) and ensure
   `--approve-mcps` is on. Mirror the intent of the hermes registration. Confirm cursor's tool-name
   convention (it may need `mcp__sources__*` exactly, or a translation like hermes' single-underscore form).
3. Verify cursor returns a parseable dimensional-review verdict (`{score, verdict, findings}`).

Repro (orchestrator used this):
```
cd /Users/krisztiankoos/projects/learn-ukrainian && \
.venv/bin/python -c "import sys;sys.path.insert(0,'scripts');from pathlib import Path;from wiki.review import _run_single_dim as r;a=Path('wiki/pedagogy/a1/this-and-that.md').resolve();d=r(dim='register',article_path=a,article_text=a.read_text(),primary='cursor',fallbacks=(),cwd=Path.cwd());print(d.verdict,d.score,(d.error or '')[:400])"
```

## C. Smoke tests (both adapters) — prevent silent regression
Add a lightweight test that each adapter can complete ONE trivial invoke and that the registry
model id is valid for its CLI (so a bad model id like grok-4.20 fails CI, not production — the #3151
lesson). Gate on the CLI being available (skip cleanly if not on PATH/CI), but the model-id-validity
check (registry id ∈ `grok models` for grok-build) can be a pure assertion.

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin`
2. You are launched in a worktree from `origin/main` (delegate `--worktree`). Symlink data if needed:
   `ln -sfn /Users/krisztiankoos/projects/learn-ukrainian/data ./data` (do NOT commit it).
3. Fix A (grok-build, 3 spots). Verify: a real grok-build review invoke returns a valid verdict (repro above with `primary='grok-build'`).
4. Fix B (cursor MCP wiring). Verify: cursor review returns a valid verdict.
5. Add smoke tests (C). Run `.venv/bin/python -m pytest tests/agent_runtime/ -q` (or the adapter test dir) → paste summary.
6. `.venv/bin/ruff check scripts/ tests/` → paste `All checks passed!`.
7. Commit conventional: `fix(agent-runtime): wire cursor sources-MCP + correct grok-build model id (#3151, #3087)`.
8. `git push -u origin <branch>` ; `gh pr create` (NO auto-merge — orchestrator reviews + re-runs the bakeoff).

## Evidence (#M-4 — command + cwd + raw output for every claim)
- grok-build valid verdict: the repro output line (verdict + score, not ERROR).
- cursor valid verdict: same.
- tests/lint: raw summary lines.
- pushed: `git push` + `git log -1 --oneline`; PR url from `gh pr view --json url`.
Unproven "fixed X" without command+output is treated as fabrication.
