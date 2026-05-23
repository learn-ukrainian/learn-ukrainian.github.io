# Gemini dispatch — Cursor V7 writer + reviewer wiring (Phase 3 of 3)

## Mission

Wire `cursor-tools` into V7's writer + reviewer pipeline so `v7_build.py --writer cursor-tools` produces a real module via `composer-2.5` (writer) with `grok-4.20-reasoning` (reviewer, also via Cursor CLI). Includes per-build scoped `.cursor/mcp.json` materialization (so MCP discipline isn't dependent on global config), `SELF_REVIEW_DETECTED` gate hardening (so same-model self-review is caught), and full observability/test parity with existing writer registrations.

**Phase 3 of 3.** Phases 1 (bridge) and 2 (runtime adapter) ship first. **DO NOT fire this dispatch until both prior PRs are merged to main and the worktree branches from a main HEAD that contains them.**

**Quality bar:** every claim tool-backed (#M-4). Test-discovery before code (#2253 fix; Step 2 below). HARD on `SELF_REVIEW_DETECTED` hardening — the merge gate proves it works.

## Required preconditions before firing this dispatch

The orchestrator firing this dispatch MUST verify on main HEAD:

1. PR #2252 merged (bridge `ab ask-cursor`) — commit on main `c6d4345119` or descendant.
2. Phase 2 PR merged (runtime adapter) — `git log --oneline | grep 'cursor adapter'` returns a hit.
3. `delegate.py --agent cursor --dry-run` parses on the main HEAD.

If any precondition fails, hold the dispatch and surface to user.

## Design spec — READ FIRST (full document)

`docs/dispatch-briefs/2026-05-23-cursor-phase-2-3-v7-writer-reviewer-design.md` is the load-bearing spec. The "Orchestrator review — incorporated before dispatch" block at the top of that doc lists three non-negotiables, two of which are Phase 3:

- **§4 `_model_family` hardening is REQUIRED** (not "recommended"). Acceptance criterion: `composer-2.5` builder + `composer-2.5` reviewer **must** emit `SELF_REVIEW_DETECTED` after this PR. Implement Option A (extend `_model_family`), Option B (exact-model fallback when both families are `None`), or both. Plus add the V7 build-time `assert WRITER_DEFAULTS[w]["model"] != REVIEWER_DEFAULTS[r]["model"]`.
- **§3 workspace dir wiring** — scoped `.cursor/mcp.json` must land under `module_dir` (build worktree), never `PROJECT_ROOT`. `_runtime_tool_config(..., workspace_dir: Path)` is a required signature change.

Phase 3 scope:
- §3 (MCP discipline at writer invocation) — entire section
- §4 (Writer-isolation gate compatibility) — entire section, including REQUIRED hardening + V7 reviewer-pairing fix
- §5 (`PROMPT_BY_WRITER` entry) — share `linear-write.md` (do not add a variant unless empirical bakeoff demands)
- §6 → "Phase 3 — pipeline wiring", "Phase 3 — reviewer / self-review policy"
- Files listed in "Files touched in implementation" grep-driven table

## Reference patterns — READ BEFORE WRITING CODE

| Pattern | Where | Why read |
|---|---|---|
| `_ensure_codex_writer_home()` | `linear_pipeline.py` ~L2942–3051 | The exact pattern Cursor mirrors — scoped MCP home via env override. Cursor's parallel is workspace-local `.cursor/mcp.json`. |
| `_runtime_tool_config()` | `linear_pipeline.py` ~L3054–3162 | The dispatch table you extend with a `cursor-tools` branch. Note the existing `codex-tools` branch is the model. |
| `WRITER_CHOICES` / `WRITER_DEFAULTS` | `linear_pipeline.py` L69–89 | The tables that need `cursor-tools` rows. |
| `REVIEWER_CHOICES` / `REVIEWER_DEFAULTS` | `linear_pipeline.py` L109–126 | Reviewer-side table — needs `cursor-tools` with `grok-4.20-reasoning` model. |
| `WRITER_SPECIFIC_DIRECTIVES` | `linear_pipeline.py` L96–107 | `agy-tools` block is the closest precedent for `cursor-tools` directive text. |
| `_reviewer_for_writer()` | `v7_build.py` L651–656 | The mapping that defaults `cursor-tools` → `claude-tools` today (wrong); Phase 3 fixes to `cursor-tools` → `cursor-tools` (same agent, different model via REVIEWER_DEFAULTS). |
| `_model_family()` | `scripts/audit/checks/review_gaming.py` L691–702 | The function getting REQUIRED hardening per §4. |
| `TestCheckCrossAgentReview` / `TestModelFamily` | `tests/test_coverage_audit_pipeline.py` L392–455 | Test classes you extend with composer-2.5 / grok-4.20-reasoning / same-model cases. |
| `test_runtime_tool_config_codex_tools_scoped_codex_home` | `tests/test_mcp_init_observability.py` ~L249+ | Mirror for `test_runtime_tool_config_cursor_tools_scoped_workspace`. |

## #M-4 deterministic preamble — verifiable claims and tools

| Claim | Tool to ground it |
|---|---|
| "Codex writer-home pattern at L2942 is X" | `sed -n '2942,3000p' scripts/build/linear_pipeline.py` + paste |
| "_model_family today only knows google/anthropic/openai" | `grep -A12 'def _model_family' scripts/audit/checks/review_gaming.py` + paste |
| "Reviewer map today defaults cursor → claude-tools" | `grep -A8 '_reviewer_for_writer' scripts/build/v7_build.py` + paste |
| "Tests touching every file I changed all run" | Step 2 discovery output + raw pytest summary |
| "SELF_REVIEW_DETECTED hardening works" | `pytest tests/test_coverage_audit_pipeline.py::TestCheckCrossAgentReview -v` raw, must show composer+composer FAILS the gate post-change |
| "Scoped workspace lands under tmp_path, not repo root" | `pytest tests/test_mcp_init_observability.py::test_runtime_tool_config_cursor_tools_scoped_workspace -v` raw |
| "V7 dry-run accepts --writer cursor-tools" | `.venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run --writer cursor-tools 2>&1 \| tail -30` raw |
| "Lint clean" | `.venv/bin/ruff check <files>` + raw `All checks passed!` |

## Steps

1. **Verify preconditions** (above) before any code work. `git log --oneline -20` to confirm Phase 1 + Phase 2 commits on main. If not, STOP and report.

2. **Test-discovery (the #2253 fix — non-negotiable).** Before writing code, list every test file referencing the files you'll touch:

   ```bash
   for f in \
     scripts/build/linear_pipeline.py \
     scripts/build/v7_build.py \
     scripts/audit/checks/review_gaming.py; do
     echo "=== tests referencing $f ==="
     grep -rl "$(basename $f .py)" tests/ 2>/dev/null
   done
   echo "=== seminar-specific test files ==="
   ls tests/curriculum/ 2>/dev/null
   ```

   Paste raw output. The list MUST include `tests/curriculum/test_seminar_plan_refs_titles.py` (or sibling) — that's the test class that produced the #2250 → #2253 chain. Every file in your discovery list runs as part of Step 13.

3. Read the design spec §3 + §4 + §5 + §6-Phase-3 in full. Read the 9 reference files / patterns listed above. Quote relevant sections in your commit body.

4. **Implement `_ensure_cursor_writer_workspace()`** in `scripts/build/linear_pipeline.py` near `_ensure_codex_writer_home()` (~L2942). Signature + body per spec §3 sketch (L210–244):

   ```python
   def _ensure_cursor_writer_workspace(
       cwd: Path,
       *,
       event_sink: Callable[..., None] | None = None,
   ) -> Path:
       """Materialize scoped .cursor/mcp.json for V7 cursor-tools writer."""
       cursor_dir = cwd / ".cursor"
       cursor_dir.mkdir(parents=True, exist_ok=True)
       config_path = cursor_dir / "mcp.json"
       desired = '{\n  "mcpServers": {\n    "sources": {\n      "url": "http://127.0.0.1:8766/mcp"\n    }\n  }\n}\n'
       if not config_path.exists() or config_path.read_text(encoding="utf-8") != desired:
           config_path.write_text(desired, encoding="utf-8")
       _emit(event_sink, "cursor_writer_workspace_resolved",
             workspace=str(cwd.resolve()), mcp_config=str(config_path))
       return cwd.resolve()
   ```

5. **Extend `_runtime_tool_config()`** with REQUIRED signature change (spec §3 L246–276):
   - Add `*, workspace_dir: Path` keyword-only parameter. **No `PROJECT_ROOT` fallback, no env-var escape hatch.**
   - Add `cursor-tools` branch using `_ensure_cursor_writer_workspace(workspace_dir, event_sink=event_sink)`.
   - Update unknown-writer error string (L3122–3126) to mention cursor-tools.

   ```python
   elif agent_label == "cursor-tools":
       agent_kwargs = {"mcp_servers": ["sources"]}
       cursor_workspace = _ensure_cursor_writer_workspace(
           workspace_dir,
           event_sink=event_sink,
       )
       tool_config.update({
           "cursor_workspace": str(cursor_workspace),
           "approve_mcps": True,
           "cursor_mode": "plan",
           "sandbox": "enabled",
       })
   ```

6. **Update all call-sites of `_runtime_tool_config()`** to pass `workspace_dir=module_dir` (or the appropriate cwd for the build phase). Grep all callers:
   ```bash
   grep -n '_runtime_tool_config(' scripts/build/
   ```
   Update each. If any call-site doesn't have an obvious `module_dir` in scope, surface it — the design intent is that scoped config lands in the build worktree, never the live repo root.

7. **Extend `WRITER_CHOICES` / `WRITER_DEFAULTS` / `REVIEWER_CHOICES` / `REVIEWER_DEFAULTS`** in `linear_pipeline.py`:
   - `WRITER_CHOICES`: add `"cursor-tools"`
   - `WRITER_DEFAULTS["cursor-tools"]`: `{"model": "composer-2.5", ...}` mirroring existing entries' shape
   - `REVIEWER_CHOICES`: add `"cursor-tools"`
   - `REVIEWER_DEFAULTS["cursor-tools"]`: `{"model": "grok-4.20-reasoning", ...}` (different model — this is the cross-model pairing)

8. **Add `WRITER_SPECIFIC_DIRECTIVES["cursor-tools"]`** (spec §5 L428–445) — short block mandating MCP-only verification, no shell, no repo edits, fenced artifacts in stdout. Mirror `agy-tools` block at L96–107.

9. **Do NOT add `PROMPT_BY_WRITER["cursor-tools"]`** — share `linear-write.md` per spec §5 recommendation. Add a variant only if a future empirical bakeoff demands it.

10. **Update `_reviewer_for_writer()`** in `v7_build.py` L651–656 (spec §4 L391–396):
    ```python
    if writer == "cursor-tools":
        return "cursor-tools"
    ```

11. **Add build-time assert** in `_run_llm_qg` / `_run_wiki_coverage_review` (spec §4 L368–372):
    ```python
    assert WRITER_DEFAULTS[writer]["model"] != REVIEWER_DEFAULTS[reviewer]["model"], \
        f"same-model self-review forbidden: writer={writer} reviewer={reviewer}"
    ```
    Test this assert fires when contrived to: `pytest -k 'test_reviewer_assert'`.

12. **REQUIRED: harden `_model_family()`** in `scripts/audit/checks/review_gaming.py` L691–702 per spec §4 L335–372. Implement Option A (extend family map) + Option B (exact-model fallback when both families `None`) — belt + suspenders. Then extend `TestCheckCrossAgentReview` and `TestModelFamily` in `tests/test_coverage_audit_pipeline.py` with:
    - `composer-2.5` builder + `grok-4.20-reasoning` reviewer → **PASS** (cross-model via Cursor CLI)
    - `composer-2.5` builder + `composer-2.5` reviewer → **VIOLATION** (same model — the hole this PR closes)
    - `grok-4.20-reasoning` builder + `grok-4.20-reasoning` reviewer → **VIOLATION**

13. **Update v7_build.py WRITER_ALIASES** (~L34–42) to accept `cursor-tools` and the bare `cursor` alias.

14. **Update `WRITER_JSON_SCHEMAS`** (if it exists / is referenced) — likely no change needed; confirm by grep.

15. Run **all** tests discovered in Step 2 + new test additions:
    ```bash
    # venv symlinked from main checkout
    .venv/bin/python -m pytest \
      tests/test_v7_writer_dispatch.py \
      tests/test_mcp_init_observability.py \
      tests/build/test_linear_pipeline.py \
      tests/test_writer_isolation.py \
      tests/build/test_v7_build_e2e.py \
      tests/test_coverage_audit_pipeline.py \
      tests/test_determine_reviewer.py \
      tests/curriculum/test_seminar_plan_refs_titles.py \
      <any-other-files-from-step-2> \
      -q --timeout 60
    ```
    Paste raw final summary. ALL must pass. If ANY existing test fails, FIX the underlying bug — do not change the test to accommodate the regression (#1 quality rule).

16. Dry-run smoke (spec L468–473):
    ```bash
    # venv symlinked
    .venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run --writer cursor-tools 2>&1 | tail -50
    ```
    Paste raw. Expect clean — `cursor-tools` recognized, scoped workspace event emitted in dry-run trace, no traceback.

17. `.venv/bin/ruff check scripts/build/ scripts/audit/checks/review_gaming.py tests/build/ tests/test_v7_writer_dispatch.py tests/test_mcp_init_observability.py tests/test_writer_isolation.py tests/test_coverage_audit_pipeline.py tests/curriculum/` — `All checks passed!`. Paste raw.

18. **Policy doc update.** Edit `claude_extensions/rules/pipeline.md` to mention cursor as a writer/reviewer option. Keep it small — one sentence in the writer/reviewer-policy block.

19. `git add` only the files you actually changed (no `git add -A`). Confirm with `git status --short` + paste raw.

20. Commit:
    ```
    feat(pipeline): cursor-tools V7 writer+reviewer + SELF_REVIEW_DETECTED hardening (Phase 3 of cursor integration)

    Wires cursor-tools (composer-2.5 writer + grok-4.20-reasoning reviewer, both via
    cursor-agent CLI) into V7 build pipeline. Includes scoped .cursor/mcp.json
    materialization under build worktree (not PROJECT_ROOT), build-time same-model
    self-review assert, and _model_family hardening so composer+composer (and any
    same-model pair) emits SELF_REVIEW_DETECTED.

    Phase 1 (bridge): PR #2252 / c6d4345119.
    Phase 2 (runtime adapter): PR #XXXX / <sha>.
    Design spec: docs/dispatch-briefs/2026-05-23-cursor-phase-2-3-v7-writer-reviewer-design.md
    ```

21. `git push -u origin <branch>`

22. `gh pr create --title "feat(pipeline): cursor-tools V7 writer+reviewer + SELF_REVIEW_DETECTED hardening — Phase 3" --body "<summary + spec link + dry-run smoke + test summary + tests-discovered list>"`

23. **NO auto-merge.** Orchestrator reviews + merges.

## Hard scope limits

In-scope:
- `scripts/build/linear_pipeline.py` (the listed functions only)
- `scripts/build/v7_build.py` (`WRITER_ALIASES`, `_reviewer_for_writer`, `_run_llm_qg`/`_run_wiki_coverage_review` assert)
- `scripts/audit/checks/review_gaming.py` (`_model_family` hardening)
- All listed test files
- `claude_extensions/rules/pipeline.md` (one-sentence policy update)

Out-of-scope (do NOT touch):
- `scripts/agent_runtime/` (Phase 2 territory)
- `scripts/ai_agent_bridge/` (Phase 1 territory)
- `scripts/build/phases/linear-write.md` — only if you'd add a `cursor-tools` variant, and spec §5 says don't unless bakeoff demands. SKIP.
- Live `.cursor/mcp.json` in repo root — do NOT modify the global config; scoped config lives only in build worktrees via `_ensure_cursor_writer_workspace`.

## Acceptance criteria

1. `v7_build.py a1 my-morning --dry-run --writer cursor-tools` exits 0 with `cursor_writer_workspace_resolved` event in trace.
2. `tests/test_coverage_audit_pipeline.py::TestCheckCrossAgentReview` passes with:
   - composer-2.5 + grok-4.20-reasoning → PASS
   - composer-2.5 + composer-2.5 → VIOLATION
3. `tests/test_mcp_init_observability.py` includes a new `test_runtime_tool_config_cursor_tools_scoped_workspace` that asserts config path is under `tmp_path`, never repo root.
4. Build-time `assert` in `_run_llm_qg` fires when writer/reviewer models match (verified by a targeted test).
5. All tests discovered in Step 2 + new tests pass. ruff clean.
6. No out-of-scope file changes.
7. PR body cites: design-spec link, tests-discovered list, dry-run smoke raw, test summary raw, both `_model_family` Options (A + B) demonstrated in tests.

## Estimated LOC budget

~350–450 LOC total (cursor's "~250" estimate was tight given REQUIRED hardening):
- `_ensure_cursor_writer_workspace`: ~30 LOC
- `_runtime_tool_config` extension + signature change + call-site updates: ~50–80 LOC
- WRITER/REVIEWER tables + directives: ~40 LOC
- `_reviewer_for_writer` + build-time assert: ~20 LOC
- `_model_family` Option A + B: ~30 LOC
- Tests (new + extended across 5+ files): ~150–200 LOC
- Policy doc + WRITER_ALIASES: ~10 LOC

Over 500 LOC → STOP and re-scope. Likely you added a writer prompt variant against spec.

---

## Related docs

- Design spec (full): `docs/dispatch-briefs/2026-05-23-cursor-phase-2-3-v7-writer-reviewer-design.md`
- Phase 1: `docs/dispatch-briefs/2026-05-23-cursor-phase-1-bridge-gemini.md`
- Phase 2: `docs/dispatch-briefs/2026-05-23-cursor-phase-2-runtime-adapter-gemini.md`
- V7 design SSOT: `docs/best-practices/v7-design-and-corpus.md`
- Pipeline policy: `claude_extensions/rules/pipeline.md`
- Self-review policy: same doc, "An LLM must NEVER review its own work."
