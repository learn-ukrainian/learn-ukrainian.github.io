# gemini-tools cwd fix — Option A from audit

**Predecessor (read first):** `audit/gemini-tools-review-2026-05-09/REPORT.html` (currently in PR #1817; if not yet merged, read from worktree `.worktrees/dispatch/codex/gemini-tools-deep-review-2026-05-09/audit/gemini-tools-review-2026-05-09/REPORT.html`).

**Root cause established by that audit:** Gemini-tools writers are invoked with `cwd=module_dir` (the bakeoff artifact directory). That directory has no `.gemini/settings.json`. Gemini CLI loads MCP servers from cwd's settings file, so it loaded none. The pipeline then passes `--allowed-mcp-server-names sources` as a filter — but the filter applies on top of an empty catalog. Result: model sees zero `mcp__sources__*` tools, model uses no MCP, `writer_tool_calls.json` ends up `[]`.

**This dispatch implements the audit's Option A fix.** Narrow Gemini-only patch. Do NOT broaden scope without explicit user signoff.

## Worktree instructions (mandatory)

```bash
git worktree add -b codex/gemini-tools-cwd-fix-2026-05-09 .worktrees/codex-gemini-tools-cwd-fix
cd .worktrees/codex-gemini-tools-cwd-fix
```

Per `.claude/rules/delegate-must-use-worktree.md`. Do NOT branch in the main checkout.

## The patch (from audit "Patch Sketch")

```python
# scripts/build/v7_build.py
writer_cwd = linear_pipeline.PROJECT_ROOT if writer == "gemini-tools" else module_dir
writer_output = linear_pipeline.invoke_writer(
    prompt,
    writer,
    cwd=writer_cwd,
    tool_trace_path=module_dir / "writer_tool_calls.json",
    stdout_silence_timeout=args.writer_timeout,
)
```

This sketch is your **starting point**, not the final patch. Adapt to the real code:

1. Read `scripts/build/v7_build.py` and find the actual `invoke_writer(...)` call site. The sketch may not match exact arg names — match what's there.
2. Check whether `linear_pipeline` exports `PROJECT_ROOT` already, or if it lives in a different module. If neither has it, derive it from the repo root the same way `linear_pipeline` does (likely `Path(__file__).parent.parent.parent` or similar).
3. Confirm `tool_trace_path` is already an explicit parameter of `invoke_writer` — that's load-bearing, since it's how the writer's tool-call telemetry survives the cwd switch (the writer is launched from repo root, but its trace file still lands in the per-module artifact directory).
4. Add an inline comment at the cwd ternary explaining why Gemini is special-cased — point at the audit report path so the next reader has the context.
5. **Do not generalize to all `*-tools` writers in this PR.** That's an audit Open Question (E5 / "Should v7 standardize all writers on repo-root cwd"). The narrow fix avoids regressing Claude-tools / Codex-tools.

## Acceptance criteria

1. **Code change in `scripts/build/v7_build.py`** wires `cwd=PROJECT_ROOT` only for `writer == "gemini-tools"`. All other writers keep `cwd=module_dir` (or whatever they had before).
2. **Inline comment** at the change explains: *"gemini-tools must load .gemini/settings.json from repo root; module_dir cwd would leave its MCP catalog empty. See audit/gemini-tools-review-2026-05-09/REPORT.html E5/E6."*
3. **Unit test** in `tests/` (likely `tests/test_v7_build.py` or `tests/test_pipeline_v7.py` — pick whichever already covers v7_build invocations): for `writer == "gemini-tools"`, assert v7_build passes `cwd=PROJECT_ROOT` to `invoke_writer`. For all other writers, assert it passes `cwd=module_dir`. Use `mock.patch` on `invoke_writer` and inspect call args.
4. **Smoke validation** (no full bakeoff — user runs builds): from repo root, run `gemini mcp list` and verify `sources` is reported as connected. Document the output in the PR body. Then `cd /tmp && gemini mcp list` (or any non-repo cwd) and confirm `sources` is NOT reported. That's the empirical proof the cwd matters.
5. **Pre-commit hygiene:** `.venv/bin/ruff check scripts/build/v7_build.py tests/<your_test_file>.py` and `.venv/bin/python -m pytest tests/<your_test_file>.py -v` both pass.
6. **Commit + push + PR:**
   - One commit: `fix(v7): gemini-tools writer cwd=PROJECT_ROOT so .gemini/settings.json loads (#1809)`
   - Push to `origin codex/gemini-tools-cwd-fix-2026-05-09`
   - `gh pr create --title "fix(v7): gemini-tools writer cwd=PROJECT_ROOT (#1809)" --body "<body referencing audit + patch + smoke evidence>"`
7. **Do NOT auto-merge.** Per `.claude/rules/non-negotiable-rules.md` and #M-0.5, only the orchestrator merges, and only after blocking CI passes.

## Out of scope (file as separate issues if compelling, do NOT include in this PR)

- **Telemetry parser fix** for `GeminiAdapter.parse_response` missing tool_calls in JSONL (audit E9). Important but separable; one fix per PR.
- **Generalizing cwd=PROJECT_ROOT to all writers** (audit Open Question 2). Needs separate evaluation; do not regress Claude/Codex.
- **Writing writer_prompt.md before invocation** so failed runs preserve the prompt artifact (audit Open Question 3). Worth doing but not blocking.
- **Stage `.gemini/settings.json` into module_dir at bakeoff time** as a defense-in-depth alternative to changing cwd. Discussed in audit Recommended Fix as Option B; rejected by Codex in favor of Option A. Don't second-guess that without rerunning the audit.

## Reference

- Audit (canonical, HTML): `audit/gemini-tools-review-2026-05-09/REPORT.html`
- Audit's E6 (the broken code path traced exactly): same file, search "E6. Code path that creates the broken delivery"
- Codex-tools sister fix that established the runtime-gate pattern: PR #1813 (`scripts/agent_runtime/tool_config.py` _codex_sanitize_server_config + linear_pipeline positive runtime gate)
- Issue: #1809 (gemini-tools wiring)

Effort: medium (small mechanical patch + 1 unit test). Model: default (gpt-5.5). No `--model` override.
