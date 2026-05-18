# Dispatch brief — Issue #2127: PR3 corrector violated `<fixes>`-only contract + YAML guard miss

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952)
**Issue:** #2127
**Severity:** HIGH (cascade risk — every module that needs wiki_coverage correction hits this; affects nearly every A1/A2 build with strict 18+ obligations)
**Sibling open issues:** none directly; tightly coupled to the Path 3 correction architecture (#2123)

---

## Why

m20 build #1 (worktree `.worktrees/builds/a1-my-morning-20260517-234227/`) reached `wiki_coverage_gate` correction iteration 2, but the corrector's output broke `activities.yaml` shape. The pipeline died with raw `yaml.YAMLError` ("mapping values are not allowed here…line 214, column 21") instead of triggering the expected `wiki_coverage_correction_yaml_invalid` rollback path.

### Bug 1 — corrector regenerated content instead of emitting `<fixes>` pairs

PR3 (#2123) brief required: *"Reviewer emits `<fixes>` block only — strict ADR-007 contract enforcement. NO regeneration. NO section-level synthesis."*

Empirical diff between `.wiki_correction_backup/batched_iter_1/activities.yaml` and the post-correction `activities.yaml`:

- Rewrote 3 EXISTING activity entries (lines 205-207, 210-212, 218-220).
- **ADDED 2 brand-new activities** (`act-8` true-false "Перевір вимову", `act-9` quiz "Транзитивне чи зворотне?").
- INSERTED 3 new `- sentence: Вимова: ...` contrast-pair entries.

That isn't find/replace — the corrector authored multi-line YAML blocks. The prompt template at `scripts/build/phases/linear-correction-wiki-coverage.md` does say `<fixes>`-only, but the model treated the obligation gap as a hole to fill rather than a delta to surgically patch.

### Bug 2 — YAML guard ran but did not catch the broken scalar

The pipeline DOES have a validator at `scripts/build/linear_pipeline.py:4232` (`_validate_wiki_coverage_artifact_text`) wired into `_apply_wiki_coverage_fixes` at line 4190 — on validator failure it rolls back from `.wiki_correction_backup/` and emits `wiki_coverage_correction_yaml_invalid`. Yet the malformed write reached the wiki_coverage_gate re-run, which means one of:

1. **PyYAML lenient parse** — `yaml.safe_load` of the malformed text returned without raising. `Вимова: [прокидайешся]` MIGHT parse as a plain scalar string in some PyYAML versions when it appears as a value of an already-keyed entry. Repro inline before writing fixes:
   ```python
   import yaml
   yaml.safe_load("- sentence: Вимова: [прокидайешся]\n  error: x\n")
   ```
2. **Validator too shallow** — current validator only checks `isinstance(parsed, list)` + `all(isinstance(item, dict) for item in parsed)`. A scalar that round-trips as a string-with-colons passes both checks but breaks downstream consumers that re-parse the file with stricter expectations.
3. **Different code path** — the broken write came from `_apply_python_qg_correction` (line 4464) which writes without calling `_validate_wiki_coverage_artifact_text`. Less likely given the gate that failed was `wiki_coverage_gate`, but verify the call site.

Whichever hypothesis is correct, the fix is the same: harden the validator to round-trip-and-dump, and put the same hardening on every artifact-writing correction path.

This cascade-blocks any module that requires wiki_coverage_gate corrections — which is most A1/A2 modules with the strict 18+ obligation count.

---

## What you build

### Two-pronged fix: corrector prompt tightening + pipeline-side validator hardening

Either prong alone leaves a gap. Prompt tightening keeps the model in the right shape; validator hardening makes regressions visible upfront instead of as raw `yaml.YAMLError` later in the pipeline.

### 1. Tighten corrector prompt template

In `scripts/build/phases/linear-correction-wiki-coverage.md` (and the sibling `linear-correction-wiki-coverage-narrow.md`):

1. Add an explicit **"You may emit ONLY"** section near the top:
   > You may emit ONLY these two fix shapes inside `<fixes>...</fixes>` (XML or YAML, no other content):
   > - `<fix><find>...</find><replace>...</replace></fix>` — local textual find/replace
   > - `<fix><insert_after>...</insert_after><text>...</text></fix>` — inserts AFTER an existing anchor
   >
   > You MUST NOT:
   > - Regenerate full activity blocks (`- id: act-N` with multiple keys).
   > - Add new top-level activity entries.
   > - Rewrite multi-line YAML structures.
   > - Output any Markdown, prose, or YAML outside `<fixes>`.

2. Add a **size-limit constraint**:
   > Each `<replace>` and each `<text>` body MUST be ≤ 6 lines OR ≤ 240 characters (whichever fires first). Larger fixes are evidence of regeneration; if you find yourself needing one, abort with `<fixes></fixes>` (empty) and let the next gate iteration handle it.

3. Add an **anti-pattern callout** with the m20 build #1 case:
   > ❌ WRONG (regeneration):
   > ```yaml
   > - find: |
   >     - id: act-7
   >       ...existing block...
   >   replace: |
   >     - id: act-7
   >       ...rewritten block...
   >     - id: act-8           # ← FORBIDDEN: brand-new entry
   >       type: true-false
   >       ...
   > ```
   > ✅ RIGHT (additive via insert_after):
   > ```yaml
   > - insert_after: |
   >     # last item of an existing activity's `items:` list
   >   text: |
   >     - left: foo
   >       right: bar
   > ```

4. Apply the same changes to `linear-correction-wiki-coverage-narrow.md`.

### 2. Pipeline-side fix-shape validator (enforces the prompt size limit)

In `scripts/build/linear_pipeline.py`, after `_parse_reviewer_fixes(response)` returns the parsed list and BEFORE applying:

```python
def _validate_reviewer_fix_shapes(fixes: list[dict[str, str]], *, max_lines: int = 6, max_chars: int = 240) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Split parsed fixes into (accepted, rejected_oversize).

    A fix is rejected when its `replace` or `text` body exceeds the size
    limit — evidence of regeneration per the corrector prompt contract.
    """
```

Emit a new event `reviewer_fix_oversize_rejected` with `{gate, group_key, body_len, line_count, body_preview}` for each rejection. Wire it into both `_apply_wiki_coverage_fixes` and `_apply_python_qg_correction` paths so the contract is enforced uniformly.

### 3. Harden `_validate_wiki_coverage_artifact_text`

Current shape (linear_pipeline.py:4232):

```python
def _validate_wiki_coverage_artifact_text(artifact: str, text: str) -> None:
    if artifact != "activities.yaml":
        return
    parsed = yaml.safe_load(text)
    if not isinstance(parsed, list):
        raise LinearPipelineError("activities.yaml must remain a bare YAML list")
    if not all(isinstance(item, dict) for item in parsed):
        raise LinearPipelineError("activities.yaml entries must remain mappings")
```

Strengthen by:

1. **Add a round-trip dump + reload check** to surface scalar-with-colon ambiguity:
   ```python
   redumped = yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False)
   reparsed = yaml.safe_load(redumped)
   if parsed != reparsed:
       raise LinearPipelineError("activities.yaml does not round-trip cleanly — likely scalar/mapping ambiguity (e.g. unquoted value containing ': ')")
   ```
2. **Per-item shape validation** for the well-known activity-type fields. The current validator accepts a dict of arbitrary shape. Tighten so each entry MUST have a non-empty string `id`, a non-empty string `type`, and (if present) `items` must be a list of dicts. This catches the "scalar that parsed as a one-key dict" failure mode.
3. **Extend coverage to `vocabulary.yaml` and `resources.yaml`** (both are also list-of-dict YAML in the wiki_coverage corrections set). Mirror the same checks.
4. **Module.md special case**: validate that any `<!-- INJECT_ACTIVITY: act-N -->` markers point at activity ids present in `activities.yaml`. Out of scope if it expands the diff too much — file follow-up if so.

### 4. Wire validator into the other write path

In `_apply_python_qg_correction` (line 4464), after `module_path.write_text(result.text, ...)` at line 4472, call the validator if the path is a YAML artifact. Without this the python_qg correction path can still write broken YAML undetected.

### 5. Tests — `tests/build/test_wiki_coverage_correction_yaml_guard.py`

Mandatory test cases (8+):

1. **Oversize `<replace>` rejected** — synthesize a fix with a 10-line replace body; assert `_validate_reviewer_fix_shapes` rejects it and emits `reviewer_fix_oversize_rejected`.
2. **Oversize `<text>` (insert_after) rejected** — same shape, insert_after variant.
3. **Within-limit fix accepted** — 3-line replace, assert acceptance.
4. **`activities.yaml` with `Вимова: [прокидайешся]` style scalar** — feed the exact malformed text from m20 build #1; assert `_validate_wiki_coverage_artifact_text` now raises.
5. **`activities.yaml` with valid shape** — assert no raise (regression guard).
6. **Round-trip mismatch** — synthesize a YAML where `safe_load(text) != safe_load(safe_dump(safe_load(text)))`; assert raise.
7. **End-to-end: corrector emits oversize fix → `_apply_wiki_coverage_fixes` rolls back** — backup is preserved, original file restored, rejection event emitted, no broken artifact on disk.
8. **End-to-end: corrector emits valid fix → applied + new validator runs + ok**.

### 6. Documentation update

In `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` (or the related Path 3 ADR), append a "Corrector contract enforcement" note pointing at the new validator + size limit.

---

## Verifiable claims (per #M-4)

| Claim | Tool + raw output |
|---|---|
| Corrector prompt updated | `git diff origin/main -- scripts/build/phases/linear-correction-wiki-coverage*.md` showing the "You may emit ONLY" + size-limit + anti-pattern sections |
| Fix-shape validator added | `git diff origin/main -- scripts/build/linear_pipeline.py` showing `_validate_reviewer_fix_shapes` + wiring |
| YAML validator hardened | same diff showing `_validate_wiki_coverage_artifact_text` round-trip + per-item checks |
| Python_qg correction path now validates | same diff showing the new call site after `_apply_python_qg_correction`'s write |
| New tests pass | `.venv/bin/pytest tests/build/test_wiki_coverage_correction_yaml_guard.py -v` final summary raw |
| Existing pipeline tests still pass | `.venv/bin/pytest tests/build/ tests/audit/ tests/test_linear_pipeline_wiki_coverage.py -q` final summary raw |
| Full pytest green | `.venv/bin/pytest tests/ -q` final summary raw (NO `-x` per #1942) |
| Ruff clean | `.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/build/phases/ tests/build/test_wiki_coverage_correction_yaml_guard.py` raw |
| Pre-commit clean | `.venv/bin/python -m pre_commit run --files <changed>` raw |
| m20 worktree replay** | Run the new validator against `.worktrees/builds/a1-my-morning-20260517-234227/curriculum/l2-uk-en/a1/my-morning/activities.yaml` (the broken file) — assert it now raises `LinearPipelineError`. Quote the exception message. Then run against the `.wiki_correction_backup/batched_iter_1/activities.yaml` (the clean baseline) — assert it does NOT raise. |
| Commit + PR | `git log -1 --oneline` + `gh pr view --json url` raw |

**No claim allowed without its raw output line.** Per #M-4.

** For the m20 replay claim: invoke `_validate_wiki_coverage_artifact_text` directly via a one-shot Python repl that reads both files. Don't rebuild the module — only re-run the validator. This is a deterministic test that the fix would have caught the build #1 failure.

---

## Worktree setup

Branch: `fix/2127-pr3-corrector-contract-and-yaml-guard`. Path: `.worktrees/dispatch/codex/2127-pr3-corrector-yaml-guard-<timestamp>/`.

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/build/test_wiki_coverage_correction_yaml_guard.py -v
.venv/bin/pytest tests/build/ tests/audit/ -q
.venv/bin/pytest tests/ -q
.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/build/phases/ tests/build/
.venv/bin/python -m pre_commit run --files \
    scripts/build/linear_pipeline.py \
    scripts/build/phases/linear-correction-wiki-coverage.md \
    scripts/build/phases/linear-correction-wiki-coverage-narrow.md \
    tests/build/test_wiki_coverage_correction_yaml_guard.py
# m20 worktree replay (READ-ONLY — does NOT rebuild module).
# venv symlinked from main; run from worktree root
.venv/bin/python -c "
from pathlib import Path
from scripts.build.linear_pipeline import _validate_wiki_coverage_artifact_text, LinearPipelineError
broken = Path('/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260517-234227/curriculum/l2-uk-en/a1/my-morning/activities.yaml')
clean = broken.parent / '.wiki_correction_backup' / 'batched_iter_1' / 'activities.yaml'
try:
    _validate_wiki_coverage_artifact_text('activities.yaml', broken.read_text(encoding='utf-8'))
    print('UNEXPECTED: broken file passed validator')
except LinearPipelineError as exc:
    print('GOOD: broken caught:', str(exc)[:300])
try:
    _validate_wiki_coverage_artifact_text('activities.yaml', clean.read_text(encoding='utf-8'))
    print('GOOD: clean file passed validator')
except LinearPipelineError as exc:
    print('UNEXPECTED: clean rejected:', str(exc)[:300])
"
git diff --stat origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.
Per #1942: NO `-x` flag.

## Commit + PR

Conventional commit. Title: `fix(build): tighten PR3 corrector contract + harden YAML guard (#2127)`. Body covers:
1. Root cause (two bugs: contract violation + lenient validator)
2. Three-part fix (prompt tightening + fix-shape validator + YAML validator hardening + python_qg path coverage)
3. m20 worktree replay outcomes (quote both `print()` lines)
4. All verifiable-claims raw outputs

NO `--auto-merge`.

## Out of scope

- Don't redesign the correction architecture — Path 3 stays; we're hardening it, not replacing it.
- Don't extend the validator to `module.md` cross-references in this PR (filed as follow-up if useful).
- Don't change `WIKI_COVERAGE_PATCHABLE_ARTIFACTS` — the artifact set is correct.
- Don't touch the python_qg gate logic itself — only the correction-write validation.
- Don't roll back PR3 — the architecture is sound; the bugs are at the prompt + validator layer.

## Anti-fabrication preamble

If anything in this brief surprises you when you read the code:

- `_validate_wiki_coverage_artifact_text` is NOT called from `_apply_wiki_coverage_fixes` (it should be — line 4190 of linear_pipeline.py — if not, the bug is "validator never wired", not "validator too lenient")
- `_apply_reviewer_fixes` write at line 4472 already round-trips through a validator and I missed it
- the corrector prompt template path is different from `scripts/build/phases/linear-correction-wiki-coverage*.md`
- the broken-file worktree at `.worktrees/builds/a1-my-morning-20260517-234227/` no longer exists or is in a different state

STOP and quote the surprise verbatim before patching.

If `yaml.safe_load` of the m20 broken `activities.yaml` actually RAISES instead of returning a malformed-but-list shape, the hypothesis is wrong and Bug 2 needs a different diagnosis — most likely the validator IS missing from one of the two correction write paths. In that case, focus on wiring coverage rather than lenience-hardening.

## Notes for orchestrator (Claude, not Codex)

* This is the second-highest-cascade-risk tech debt currently open per the inventory check tonight (after #2128 vesum which is firing now).
* Estimated duration: 45-60 min (medium scope: 2 prompts + 2 helpers + 8 tests + 1 doc update).
* **DO NOT FIRE while #2128 is in flight** — both touch `scripts/build/linear_pipeline.py`. Wait for #2128 to merge, then fire #2127. Otherwise both branches will conflict at the `_apply_wiki_coverage_fixes` / `_activity_vesum_text` lines.
* On finalize: verify m20 worktree replay output is included in PR body — that's THE proof the validator now catches the regression.
* AFTER merge: re-fire m20 v7_build to see if the architecture ships m20 E2E. If `wiki_coverage_gate` now correctly rolls back invalid corrector output AND the corrector itself stays in-shape, the module should pass through the gate (or fail with a CLEAN obligation message, not a YAML stacktrace).
