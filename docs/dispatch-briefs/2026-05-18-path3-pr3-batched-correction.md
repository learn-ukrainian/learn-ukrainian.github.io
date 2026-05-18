# Dispatch brief — Path 3 PR3: batched wiki_coverage correction pass

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952, enforced by `delegate.py dispatch`)
**Scope:** PR3 of 4 in Path 3 architecture per
`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` lines 66-92.
Add a batched correction wrapper around `run_wiki_coverage_gate` modeled on
`run_python_qg_with_corrections` (already in `linear_pipeline.py`). PR4
(Goodhart sentinel) is OUT of scope; the existing
`_run_wiki_coverage_review` in `v7_build.py` already covers semantic
adequacy and PR4 will refine that prompt, not add a new pass.

---

## Why

`scripts/build/v7_build.py:805-806` currently raises
`LinearPipelineError("Wiki coverage gate failed")` the instant the
deterministic gate reports `passed=False`. On m20-my-morning that fires
at coverage 44% (8/18 obligations) — the single-pass writer ceiling that
PR1/PR2 architected this loop to break through.

PR2 (commit `dce4064ec2`) already emits structured `fix_proposals` from
`run_wiki_coverage_gate` (linear_pipeline.py:2898-2921). PR1 (commit
`0f96f459f4`) writes `module_dir/implementation_map.json` with per-entry
`treatment_template` and verbatim `manifest_payload`. PR3 closes the loop:
group the failures, call ONE reviewer per group, apply `<fixes>` block
deterministically, re-run the gate. Cap iterations. If batched pass
plateaus, fall through to per-obligation narrow calls. After cap, emit
`plan_revision_request` and abort the build with a clean signal.

---

## What you build

### 1. New phase prompt template: `scripts/build/phases/linear-correction-wiki-coverage.md`

Mirror the shape of `scripts/build/phases/linear-review-wiki-coverage.md`
but for **correction**, not review. Required template variables:

- `{LEVEL}` `{MODULE_NUM}` `{MODULE_SLUG}` `{WORD_TARGET}` (header context, same as review)
- `{FAILURE_GROUP_KEY}` — `"(artifact=activities.yaml, obligation_type=l2_error)"` etc., the `(artifact, obligation_type)` tuple that groups failures.
- `{FIX_PROPOSALS_YAML}` — YAML dump of the list of `fix_proposals` entries IN THIS GROUP. Each entry already carries `obligation_id`, `failure_reason`, `current_artifact_state`, `expected_treatment`, `surgical_diff_hint`, `manifest_payload` (the PR2 schema). Reviewer reads this verbatim — no re-fetching, no re-derivation.
- `{ARTIFACT_TEXT}` — the current text of the failure group's artifact. For `artifact=module.md` this is the full `module.md`. For `artifact=activities.yaml` this is the full `activities.yaml`. Reviewer sees the live state, not a snippet.
- `{COVERAGE_PCT_BEFORE}` — current gate's `coverage_pct` (informational).
- `{ITERATION}` — `1`, `2`, ... (informational, lets reviewer self-pace).

The body MUST enforce:

1. Strict ADR-007: output is a single `<fixes>` block ONLY. NO regeneration. NO section rewrites. NO commentary outside `<fixes>`. Reference `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md` by path.
2. The find/replace pairs (XML form OR YAML list form — both currently supported by `_parse_reviewer_fixes` at linear_pipeline.py:3836-3891) must each target a unique substring of the current artifact text. Quote the exact prior text in `<find>`; emit the corrected text in `<replace>`.
3. For each fix, the reviewer must briefly state which `obligation_id` the fix satisfies (as a YAML/XML attribute or sibling comment per the existing parser's tolerance — check the parser; pick whichever shape it accepts WITHOUT relaxing it).
4. The fix must use the `manifest_payload` values verbatim — e.g. for `l2_error.contrast_pair`, `<replace>` MUST contain the `incorrect` and `correct` strings exactly as the manifest spells them.
5. No fix may exceed 600 characters in the `<replace>` block (Grok's "small diff" constraint — Decision Card line 80).

Cross-reference both the Decision Card and PR2 brief in the prompt's
preamble so future maintainers can reconstruct the why from the prompt
alone.

### 2. New phase prompt template: `scripts/build/phases/linear-correction-wiki-coverage-narrow.md`

For Phase 4 per-obligation fallback. Same shape as §1 but takes ONE
obligation at a time. Variables:

- `{LEVEL}` `{MODULE_NUM}` `{MODULE_SLUG}` (header context)
- `{OBLIGATION_ID}` `{OBLIGATION_TYPE}` `{FAILURE_REASON}` (single obligation)
- `{EXPECTED_TREATMENT}` `{MANIFEST_PAYLOAD}` `{SURGICAL_DIFF_HINT}` (per-obligation spec from PR2)
- `{CURRENT_ARTIFACT_STATE}` (the bounded snippet from PR2)
- `{FULL_ARTIFACT_TEXT}` (the full artifact for context — same shape as batched)
- `{PREVIOUS_BATCHED_ATTEMPTS}` — number of batched-pass iterations already attempted (informational; usually 1 or 2).

Same strict ADR-007 contract as §1. Same parser-compatibility (use only
`<find>`/`<replace>` pairs).

### 3. New context + render functions in `scripts/build/linear_pipeline.py`

Place these immediately after `render_wiki_coverage_review_prompt`
(linear_pipeline.py:3008-3024).

```python
def wiki_coverage_correction_context(
    *,
    plan: Mapping[str, Any],
    failure_group_key: str,
    fix_proposals: Sequence[Mapping[str, Any]],
    artifact_text: str,
    coverage_pct_before: float,
    iteration: int,
) -> dict[str, str]: ...

def render_wiki_coverage_correction_prompt(
    *,
    plan: Mapping[str, Any],
    failure_group_key: str,
    fix_proposals: Sequence[Mapping[str, Any]],
    artifact_text: str,
    coverage_pct_before: float,
    iteration: int,
) -> str: ...

def wiki_coverage_narrow_correction_context(
    *,
    plan: Mapping[str, Any],
    fix_proposal: Mapping[str, Any],
    artifact_text: str,
    previous_batched_attempts: int,
) -> dict[str, str]: ...

def render_wiki_coverage_narrow_correction_prompt(
    *,
    plan: Mapping[str, Any],
    fix_proposal: Mapping[str, Any],
    artifact_text: str,
    previous_batched_attempts: int,
) -> str: ...
```

`fix_proposals` is the parsed list-of-dicts from
`run_wiki_coverage_gate(...).get("fix_proposals")`. `artifact_text` is
read fresh per iteration from `module_dir / artifact_filename`. Use
`yaml.safe_dump(list(fix_proposals), allow_unicode=True, sort_keys=False)`
for the `FIX_PROPOSALS_YAML` injection.

### 4. New wrapper: `run_wiki_coverage_with_corrections` in `linear_pipeline.py`

Mirror the structure of `run_python_qg_with_corrections`
(linear_pipeline.py:3524-3604). Place immediately after it.

```python
WIKI_COVERAGE_BATCH_MAX_ITERATIONS = 2
WIKI_COVERAGE_NARROW_MAX_ITERATIONS = 2  # per obligation

def run_wiki_coverage_with_corrections(
    *,
    plan: Mapping[str, Any],
    manifest: Mapping[str, Any] | str | Path,
    writer_output: str,
    module_dir: Path,
    level: str | None = None,
    batched_corrector: Callable[..., str] | None = None,
    narrow_corrector: Callable[..., str] | None = None,
    invoker: Callable[..., Any] | None = None,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    """Run wiki_coverage_gate with batched + per-obligation correction loop.

    Returns the FINAL gate report. Caller (v7_build) decides what to do
    with `passed=False` (raise) vs `passed=True` (continue to review).
    """
```

Behavior:

1. **Initial gate run** — call existing `run_wiki_coverage_gate`. If `passed`, return immediately.
2. **Phase 3 — batched pass loop** (max `WIKI_COVERAGE_BATCH_MAX_ITERATIONS`):
   - Read `result["fix_proposals"]` (PR2-emitted list).
   - Group by `(proposal["expected_treatment"].get("artifact", ?), proposal["obligation_type"])` if available; otherwise fall back to grouping by `obligation_type` alone. **Inspect PR1's `treatment_template` schema first** (scripts/build/phases/implementation_map.py:70-100) — the `treatment_template` shape varies per `obligation_type` so the group key depends on what's actually present. If `artifact` is not on the treatment_template, group by obligation_type alone. Quote your finding in the PR body.
   - Track `coverage_pct_before = result.get("coverage_pct", 0.0)`.
   - For each group, render `render_wiki_coverage_correction_prompt(...)` and dispatch to the configured corrector. Default invocation: Codex `xhigh`, mode `read-only`, model `REVIEWER_DEFAULTS["codex-tools"]["model"]`, tool_config `_runtime_tool_config("codex-tools")` — matching the existing `_apply_reviewer_correction` shape at linear_pipeline.py:3783-3800.
   - Parse the response via existing `_parse_reviewer_fixes(...)`. If empty fixes → emit `wiki_coverage_correction_unparseable` event with same fields as `reviewer_fixes_unparseable`. Continue to next group (do NOT abort the whole pass on a single empty group).
   - Apply fixes via existing `_apply_reviewer_fixes(...)` (linear_pipeline.py — search nearby `_apply_reviewer_correction` body) on the target artifact file. Write the artifact back. **For `artifact=activities.yaml`, parse the result to confirm it remains a valid YAML list of mappings** (existing `write_writer_artifacts` does this — call the equivalent validator and on failure rollback the file write + emit `wiki_coverage_correction_yaml_invalid` event).
   - After all groups processed, re-run `run_wiki_coverage_gate`. Compute `coverage_pct_after`.
   - **Monotonicity guard (Decision Card risk #1):** if `coverage_pct_after < coverage_pct_before - 1e-6`, ROLLBACK by restoring artifacts from a per-iteration backup (write `module_dir/.wiki_correction_backup/iter_{N}/` before applying fixes), emit `wiki_coverage_correction_regression` event with `coverage_pct_before` / `coverage_pct_after` / `iteration`, and break out of batched loop (proceed to Phase 4).
   - If new gate `passed=True` → return immediately.
   - Otherwise increment iteration counter, loop.
3. **Phase 4 — per-obligation narrow loop** (max `WIKI_COVERAGE_NARROW_MAX_ITERATIONS` per obligation):
   - For each remaining failed obligation in the most recent gate report:
     - Render `render_wiki_coverage_narrow_correction_prompt(...)` and dispatch (same Codex routing as Phase 3 but `effort="high"` per Decision Card line 90).
     - Apply fixes via `_apply_reviewer_fixes`. Same YAML-validity / monotonicity guards.
     - Re-run gate ONLY after all narrow calls in this iteration complete (batch the gate-run cost). Then loop with the new failure set.
   - After cap exhausted: emit `wiki_coverage_plan_revision_request` event with full failure list, current `coverage_pct`, and `iterations_exhausted=true`. Return the gate report with `passed=False` — caller raises.
4. **Telemetry events to emit per iteration** (use `_emit(event_sink, ...)` pattern from existing code):
   - `wiki_coverage_correction_pass_start` — `phase` ("batched" / "narrow"), `iteration`, `coverage_pct_before`, `fail_count`.
   - `wiki_coverage_correction_pass_done` — same fields + `coverage_pct_after`, `fixes_applied_total`, `groups_processed` (batched only) / `obligations_processed` (narrow only).
   - `wiki_coverage_correction_regression` — `phase`, `iteration`, `coverage_pct_before`, `coverage_pct_after`.
   - `wiki_coverage_correction_unparseable` — `phase`, `iteration`, `group_key` (batched) / `obligation_id` (narrow), `response_preview` (first 800 chars).
   - `wiki_coverage_correction_yaml_invalid` — `phase`, `iteration`, `artifact`, `error_preview`.
   - `wiki_coverage_plan_revision_request` — terminal event; `coverage_pct_final`, `remaining_failures`, `total_iterations`.

`_emit` already exists in linear_pipeline.py; reuse it.

### 5. v7_build.py wiring

Replace lines 795-806 (`phase = "wiki_coverage_gate"` block + the hard raise) with:

```python
phase = "wiki_coverage_gate"
started_at = time.monotonic()
wiki_coverage_gate = linear_pipeline.run_wiki_coverage_with_corrections(
    plan=plan,
    manifest=wiki_manifest,
    writer_output=writer_output,
    module_dir=module_dir,
    level=level,
    event_sink=tracker.emit,
)
linear_pipeline.write_json(module_dir / "wiki_coverage_gate.json", wiki_coverage_gate)
_phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
if wiki_coverage_gate.get("passed") is not True:
    raise linear_pipeline.LinearPipelineError(
        "Wiki coverage gate failed after batched + narrow correction passes"
    )
```

DO NOT touch the `wiki_coverage_review` phase (lines 808-826) — that's
Goodhart sentinel territory and stays under PR4.

### 6. Tests: `tests/build/test_wiki_coverage_corrections.py`

Mandatory test cases (15 minimum):

1. **Initial pass short-circuit**: gate passes on first call → wrapper
   returns immediately, no corrector calls made, no events emitted beyond
   the existing `wiki_coverage_fix_proposals` emit (which is suppressed
   on success per PR2).
2. **Single batched pass succeeds**: gate fails initially, batched
   corrector returns fixes that make gate pass on re-run → wrapper
   returns `passed=True` with `coverage_pct_after > coverage_pct_before`.
3. **Two batched passes succeed**: first pass partial improvement,
   second pass closes the rest.
4. **Batched pass plateaus → falls through to narrow loop**: after 2
   batched passes coverage stops improving → narrow loop fires and
   succeeds.
5. **Narrow loop succeeds**: 3 remaining failed obligations after
   batched cap → narrow calls each → all 3 PASS on next gate.
6. **Narrow loop exhausted → plan_revision_request**: obligations remain
   failing after narrow cap → emit `wiki_coverage_plan_revision_request`
   event + return `passed=False`. Assert event payload includes `coverage_pct_final`, `remaining_failures`, `total_iterations`.
7. **Monotonicity rollback in batched pass**: simulate a batched
   corrector that REGRESSES coverage_pct → wrapper rolls back artifact
   files from backup, emits `wiki_coverage_correction_regression`,
   breaks out of batched loop into narrow loop.
8. **Monotonicity rollback in narrow pass**: same regression in narrow
   pass → rollback + event + skip that obligation's remaining narrow
   iterations.
9. **Unparseable batched response**: corrector returns text without
   `<fixes>` block → emit `wiki_coverage_correction_unparseable` event
   with `phase="batched"`, `group_key=<...>`, continue to next group
   (do not abort).
10. **Unparseable narrow response**: same shape for narrow phase.
11. **YAML-invalid fix**: corrector returns a fix that breaks
    `activities.yaml` shape → rollback that single artifact write +
    emit `wiki_coverage_correction_yaml_invalid` event.
12. **Group key fallback**: when `treatment_template` lacks `artifact`,
    grouping falls back to `obligation_type` alone — exercise both code
    paths.
13. **Telemetry event order**: assert events fire in expected order
    (`*_pass_start` → fixes_applied → `*_pass_done`) for a single
    successful batched pass.
14. **Verbatim manifest_payload propagation**: assert the rendered
    correction prompt contains the manifest's `incorrect`/`correct`
    strings verbatim (no transformation).
15. **Caller-injected corrector**: assert `batched_corrector=fn` and
    `narrow_corrector=fn` overrides bypass the default runtime invoker.

For test fixtures, reuse the same gate-fixture pattern as
`tests/audit/test_wiki_coverage_gate_fix_proposals.py` (PR2). Use
synthetic manifest + writer-output fixtures (no real m20 build
dependency). The `qg_runner`-style callable injection from
`run_python_qg_with_corrections` is the model — your wrapper signature
already supports it via `batched_corrector` / `narrow_corrector` /
`invoker` kwargs.

### 7. Docstring + module-doc updates

- Top of `linear_pipeline.py`: add a brief Path 3 note pointing at the
  Decision Card.
- Wrapper function docstring: name PR1 (sidecar), PR2 (fix_proposals),
  PR3 (this), PR4 (Goodhart sentinel — out of scope for this PR).

---

## Verifiable claims this PR must produce (per #M-4)

| Claim | Tool + raw output to quote in PR body |
|---|---|
| Wrapper added | `git diff --stat origin/main` showing `scripts/build/linear_pipeline.py` + the two new phase prompt files + `tests/build/test_wiki_coverage_corrections.py` |
| New unit tests pass | `.venv/bin/pytest tests/build/test_wiki_coverage_corrections.py -v` final summary line raw |
| Existing wiki_coverage tests still pass | `.venv/bin/pytest tests/audit/test_wiki_coverage_gate_fix_proposals.py tests/test_wiki_coverage_gate.py -q` final summary line raw |
| Full `tests/audit/ tests/build/` green | `.venv/bin/pytest tests/audit/ tests/build/ -q` final summary line raw (NO `-x` per #1942) |
| v7_build smoke test | `.venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run 2>&1 | grep -E '^(wiki_coverage|phase_done)' | head -20` raw output (validates wiring) |
| Ruff clean | `.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/build/v7_build.py tests/build/test_wiki_coverage_corrections.py scripts/build/phases/linear-correction-wiki-coverage.md scripts/build/phases/linear-correction-wiki-coverage-narrow.md` raw output (`.md` files lint-ignored; ruff will skip them — that's expected) |
| Pre-commit clean | `.venv/bin/python -m pre_commit run --files scripts/build/linear_pipeline.py scripts/build/v7_build.py tests/build/test_wiki_coverage_corrections.py scripts/build/phases/linear-correction-wiki-coverage.md scripts/build/phases/linear-correction-wiki-coverage-narrow.md` raw output |
| Commit landed + PR opened | `git log -1 --oneline` raw + `gh pr view --json url` raw URL |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

`delegate.py dispatch --worktree` handles the worktree creation. The
canonical shape is:

```bash
.worktrees/dispatch/codex/path3-pr3-batched-correction-<timestamp>/
```

Branch name: `feat/path3-pr3-batched-correction`.

---

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/build/test_wiki_coverage_corrections.py -v
.venv/bin/pytest tests/audit/test_wiki_coverage_gate_fix_proposals.py tests/test_wiki_coverage_gate.py -q
.venv/bin/pytest tests/audit/ tests/build/ -q
.venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run 2>&1 | grep -E '^(wiki_coverage|phase_done)' | head -20
.venv/bin/ruff check scripts/build/linear_pipeline.py \
                    scripts/build/v7_build.py \
                    tests/build/test_wiki_coverage_corrections.py
# venv symlinked from main; run from worktree root
.venv/bin/python -m pre_commit run --files \
    scripts/build/linear_pipeline.py \
    scripts/build/v7_build.py \
    tests/build/test_wiki_coverage_corrections.py \
    scripts/build/phases/linear-correction-wiki-coverage.md \
    scripts/build/phases/linear-correction-wiki-coverage-narrow.md
git diff --stat origin/main
git diff --name-only origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.
Per #1942: NO `-x` flag.

---

## Commit + PR

```bash
git add scripts/build/linear_pipeline.py \
        scripts/build/v7_build.py \
        scripts/build/phases/linear-correction-wiki-coverage.md \
        scripts/build/phases/linear-correction-wiki-coverage-narrow.md \
        tests/build/test_wiki_coverage_corrections.py
git commit -m "$(cat <<'EOF'
feat(build): Path 3 PR3 — batched wiki_coverage correction pass

Decision Card docs/decisions/2026-05-17-path3-per-obligation-review-loop.md
lines 66-92: when the deterministic wiki_coverage_gate fails, group the
PR2-emitted fix_proposals by (artifact, obligation_type), fire one Codex
xhigh reviewer call per group with strict <fixes>-only contract, apply
fixes deterministically via the existing _apply_reviewer_fixes path,
re-run gate. Cap batched iterations at 2. If failures remain, fall
through to per-obligation narrow reviewer calls (Codex high), cap 2
iterations per obligation. After full exhaust, emit
wiki_coverage_plan_revision_request and abort with a clean signal.

Per-iteration monotonicity guard (Decision Card risk #1): if
coverage_pct regresses, restore from per-iteration artifact backup, emit
wiki_coverage_correction_regression event, break out of current phase.

PR3 scope (this PR):
* New wrapper run_wiki_coverage_with_corrections in linear_pipeline.py
  modeled on run_python_qg_with_corrections.
* Two new phase prompt templates: linear-correction-wiki-coverage.md
  (batched) and linear-correction-wiki-coverage-narrow.md (per
  obligation). Both enforce strict ADR-007 <fixes>-only contract +
  verbatim manifest_payload reproduction + 600-char per-fix cap.
* New context + render helpers wiki_coverage_correction_context /
  render_wiki_coverage_correction_prompt and narrow equivalents.
* v7_build.py wiring: replace the hard raise at line 805-806 with the
  correction wrapper; downstream wiki_coverage_review phase unchanged.
* New telemetry events:
  wiki_coverage_correction_pass_start/_done,
  wiki_coverage_correction_regression,
  wiki_coverage_correction_unparseable,
  wiki_coverage_correction_yaml_invalid,
  wiki_coverage_plan_revision_request.
* 15 contract tests covering initial pass short-circuit, batched
  success/plateau/regression, narrow success/exhaust/regression,
  unparseable responses, YAML-invalid fixes, group-key fallback,
  telemetry event ordering, verbatim manifest_payload propagation,
  caller-injected corrector overrides.

Out of scope:
* PR4 Phase 5 Goodhart sentinel (existing _run_wiki_coverage_review
  in v7_build.py already covers semantic adequacy; PR4 will refine
  that prompt, not add a new pass).
* Any change to PR1's seeder, PR2's gate output schema, or the
  writer prompt.

Verification:
* tests/build/test_wiki_coverage_corrections.py: <quote pytest final line>
* tests/audit/test_wiki_coverage_gate_fix_proposals.py + test_wiki_coverage_gate.py: <quote pytest final line>
* tests/audit/ + tests/build/ full: <quote pytest final line>
* v7_build dry-run smoke: <quote stdout>
* ruff: <quote raw>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Codex <noreply@anthropic.com>
EOF
)"
git push -u origin feat/path3-pr3-batched-correction
gh pr create --title "feat(build): Path 3 PR3 — batched wiki_coverage correction pass" --body "$(cat <<'EOF'
## Summary

Third of 4 Path 3 PRs per Decision Card
`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`.

Wraps `run_wiki_coverage_gate` with a batched + per-obligation
correction loop modeled on `run_python_qg_with_corrections`. When the
deterministic gate fails, the wrapper groups the PR2-emitted
`fix_proposals` by `(artifact, obligation_type)`, fires one Codex xhigh
reviewer call per group with the strict ADR-007 `<fixes>`-only
contract, applies fixes via the existing `_apply_reviewer_fixes`
infrastructure, re-runs the gate. Cap batched iterations at 2; on
plateau or regression, fall through to per-obligation narrow calls
(Codex high) with the same fixes-only contract, cap 2 iterations per
obligation. After full exhaust, emit
`wiki_coverage_plan_revision_request` and abort the build with a
clean signal so the next plan iteration can adjust ambition.

Per-iteration monotonicity guard: if `coverage_pct` regresses after a
batched or narrow pass, the wrapper rolls back the artifact files
from a per-iteration backup, emits
`wiki_coverage_correction_regression`, and breaks out of the current
phase. This implements Decision Card risk #1 mitigation.

`_run_wiki_coverage_review` (the existing semantic-adequacy reviewer
phase in `v7_build.py`) is left untouched — PR4 will refine its
prompt to be the Goodhart sentinel rather than adding a new pass.

## Verifiable claims (per #M-4)

* `git diff --stat`: <quote>
* `tests/build/test_wiki_coverage_corrections.py`: <quote pytest final line raw>
* `tests/audit/test_wiki_coverage_gate_fix_proposals.py + test_wiki_coverage_gate.py`: <quote pytest final line raw>
* Full `tests/audit/ tests/build/`: <quote pytest final line raw>
* `v7_build.py a1 my-morning --dry-run` smoke: <quote stdout>
* `ruff check`: <quote raw>

## Test plan

* [x] Initial pass short-circuit (no correction calls when gate passes)
* [x] Batched pass — success on first iteration
* [x] Batched pass — partial improvement, success on second iteration
* [x] Batched plateau → fall through to narrow loop
* [x] Narrow loop — success / exhaust → plan_revision_request
* [x] Monotonicity rollback in both batched + narrow phases
* [x] Unparseable response / YAML-invalid fix events
* [x] Group key fallback when treatment_template lacks artifact
* [x] Telemetry event ordering
* [x] Verbatim manifest_payload propagation
* [x] Caller-injected corrector overrides

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

NO `--auto-merge`. Leave the PR open; orchestrator merges after review.

---

## Out of scope (do NOT include)

* PR4 Goodhart sentinel — DO NOT touch
  `scripts/build/phases/linear-review-wiki-coverage.md` or
  `_run_wiki_coverage_review` in v7_build.py.
* Any change to PR1's seeder (`scripts/build/phases/implementation_map.py`)
  or PR2's gate output (`scripts/audit/wiki_coverage_gate.py`). If you
  find a bug, STOP and file a follow-up issue.
* Any change to the writer prompt or `_apply_writer_correction` /
  `_apply_reviewer_correction` (these are Python QG correction paths;
  PR3 reuses `_apply_reviewer_fixes` directly, not the higher-level
  Python-QG-specific wrappers).
* External_resources obligations — out of scope per PR2's same exclusion.
* Cosmetic refactors to surrounding code beyond what the new wrapper
  needs.

---

## Anti-fabrication preamble

If anything in this brief surprises you when you actually read the code:

- the `fix_proposals` schema differs from what's described (PR2 may have
  shipped slightly different field names than the brief lists)
- `_apply_reviewer_fixes` isn't the right entrypoint for non-`module.md`
  artifacts (e.g. it hard-codes the module.md path)
- the `treatment_template` shape doesn't carry an `artifact` field
- `run_wiki_coverage_gate` already does something the brief reinvents

STOP and quote the surprise verbatim before patching. Don't paper over.
PR2 and PR1 just merged hours ago; the brief was written from a careful
read but may have a stale detail. Quote-then-adapt is better than
silent-adapt.

If `_apply_reviewer_fixes` is module.md-locked, you have two options:
(a) extract a generic `_apply_fixes_to(text, fixes) -> ApplyResult`
helper and call it for both module.md and activities.yaml paths, or
(b) duplicate the logic. Prefer (a). Quote your choice in the PR body.

If the parser at `_parse_reviewer_fixes` does NOT accept any per-fix
`obligation_id` attribution, drop the brief's §1 item 3 requirement —
the deterministic group + iteration logging on the orchestrator side is
enough. Quote the parser shape in the PR body so the next maintainer
knows the choice was deliberate.

If a test feels redundant or impossible to write deterministically, name
the specific test and the specific blocker — do not silently drop tests
from the list. Reduce-and-justify is acceptable; silent-drop is not.

---

## Notes for orchestrator (Claude, not Codex)

* Dispatch CAP: 1 Codex slot used (`adopt-kubedojo-artifacts-20260517-215941`,
  19+ min in at brief-write time). Firing PR3 takes us to 2/2 Codex slots.
  Both are mechanical-with-design-judgment; either landing first frees
  PR4 for Codex too.
* Monitor pattern per #M-8: schedule a 1200s (20 min) wakeup to poll
  `/api/delegate/active`. PR3 is the largest of the four Path 3 PRs;
  estimated duration 25-40 min based on PR2's 990s.
* On PR3 finalize: read the PR body, verify the 7 verifiable-claims raw
  outputs are quoted, check CI rollup, merge if all blocking checks green,
  delete the worktree + branch. Then write PR4 brief and fire to Codex.
