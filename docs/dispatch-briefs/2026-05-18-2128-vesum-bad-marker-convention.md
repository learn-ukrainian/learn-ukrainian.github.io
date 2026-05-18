# Dispatch brief — Issue #2128: vesum_verified false-positive on intentional teaching content

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952)
**Issue:** #2128 (revised diagnosis — see issue comment 4474996179)
**Severity:** HIGH (cascade risk — every module with `true-false` activities naming a wrong form as negative example hits this; error-correction is a core pedagogical activity type, so this blocks every m20-style ship)
**Sibling open issues:** #1975 (predates this — same underlying cause "vesum_verified malformed forms")

---

## Why

m20 build #2 (2026-05-18 02:06 worktree `a1-my-morning-20260518-000636`) failed at `python_qg.vesum_verified` with `missing: ['дивюся']`. Investigation showed the writer correctly used `дивюся` as intentional teaching content in three places:

1. `module.md:53` — `<!-- bad -->дивюся<!-- /bad -->` (WORKS today — `_strip_metalinguistic` strips markers; `_ERROR_CORRECTION_INTENTIONAL_FIELDS` not relevant for prose)
2. `activities.yaml:280-287` — `id: act-error-l2`, `type: error-correction` with `sentence: Я дивюся в дзеркало.` / `error: дивюся` / `correction: дивлюся` (WORKS today — `_activity_vesum_text` at linear_pipeline.py:5953-5958 sets `skip_subtree = _ERROR_CORRECTION_INTENTIONAL_FIELDS` which includes `"sentence"`, so the whole subtree is skipped)
3. `activities.yaml:161` — `true-false` statement:

   ```yaml
   - statement: У дієсловах другої дієвідміни 1-ша особа однини після губних має вставне 'л' — дивлюся, а не дивюся.
     answer: true
   ```

   **THIS is the gap.** TF statements with `answer: true` are walked via `walk_truefalse_statement(statement, answer)` at linear_pipeline.py:5986-5988. Statement text contains both `дивлюся` (correct) AND `дивюся` (named as negative example). Both get VESUM-checked. `дивюся` fails. Build dies.

The writer's own `verification_plan` documents the convention: *"confirm bad forms (дивюся, користуювася, мию себе) are not in VESUM so they only appear inside `<!-- bad -->` markers"* — but the writer applied the convention only in module.md prose, NOT inside the TF statement string. The gate has no enforcement.

This cascade-blocks every module that teaches a contrast via "X is correct, Y is wrong" in a TF item — a normal pedagogical pattern at every CEFR level.

---

## What you build

### Two-pronged fix: writer prompt convention + gate-side robustness

Either prong alone leaves a gap. The writer prompt change makes the writer DO the right thing; the gate-side change handles drift if the writer slips.

### 1. Writer prompt — extend bad-form marker rule to ALL artifact locations

Locate the writer prompt for `claude-tools` (likely `scripts/build/phases/linear-write.md` per the v7_build writer-prompts-path convention). Find the section that documents the `<!-- bad -->...<!-- /bad -->` convention. Extend it:

> **Bad-form marker convention (MANDATORY everywhere):**
>
> Any Ukrainian word form that is NOT in VESUM — intentional misspellings, Russianisms, Surzhyk, calques, archaisms appearing only for teaching contrast — MUST be wrapped in `<!-- bad -->...<!-- /bad -->` markers wherever it appears in the output, **regardless of which artifact**:
>
> - **module.md prose** (already required): `**дивитися → я дивлюся**, not <!-- bad -->дивюся<!-- /bad -->`
> - **activities.yaml `true-false` `statement:` fields**: any negative example named in a true statement must be marker-wrapped. WRONG: `statement: "правильно: X, а не Y."`. RIGHT: `statement: "правильно: X, а не <!-- bad -->Y<!-- /bad -->."`
> - **activities.yaml `match`, `fill-in`, `multiple-choice`, `order`, `pair-up`, etc. items**: any wrong form named as a contrast — if it's not a structural field like `error:` (which the gate already skips), it MUST have markers.
> - **vocabulary.yaml `usage:` field**: usually exemplifies the correct form, so markers shouldn't normally be needed. If a usage line names a wrong form for teaching, marker it.
> - **resources.yaml `title:` / notes**: out of scope; do not marker.
>
> The gate strips markers before VESUM lookup. Any non-VESUM word NOT inside markers will fail `vesum_verified` and block the build.
>
> **Exception**: `type: error-correction` activity items already have `sentence:` / `error:` fields fully excluded from VESUM lookup; markers are optional there but harmless.

Also add a writer **anti-pattern callout**: "True-false statements that say `X, а не Y` (X, not Y) MUST marker the Y form."

Same change in the codex-tools writer prompt (`linear-write-codex.md` or similar) and the gemini-tools writer prompt if separate. Find them via `grep -rn "<!-- bad -->" scripts/build/phases/` — apply the same rule consistently.

### 2. Gate-side — auto-detect `<!-- bad -->`-less negative-example pattern in TF statements

In `scripts/build/linear_pipeline.py`, extend `_strip_metalinguistic` (or add a sibling helper called from `_activity_vesum_text` for the TF branch only) to handle the common Ukrainian "X, а не Y" / "X, not Y" pattern:

```python
# Pattern: "..., а не <bad-form>." or "..., not <bad-form>."
# When the writer fails to wrap the bad form in markers, this saves a build
# from failing on an obvious teaching contrast.
#
# Conservative: only strips the LAST 1-3 word form after "а не " / "не " /
# "not " when it appears at sentence boundary. Bigger context strips would
# risk dropping legitimate Ukrainian words.
_TF_NEGATIVE_EXAMPLE_RE = re.compile(
    r"(?:,\s*(?:а\s+)?не|,\s*not)\s+([\w'’ʼ-]+)\s*[.!?]",
    re.UNICODE | re.IGNORECASE,
)
```

In `_activity_vesum_text`'s TF branch, before passing `statement` to the walker, identify negative-example tail forms and ADD them to a per-statement skip set (don't return them in the iterator).

**Conservatism rationale**: this only matches the explicit "X, не Y." sentence-final pattern. Multi-word negatives ("a не Y або Z") OR negative examples in the middle of a statement won't match and SHOULD still rely on the writer's `<!-- bad -->` markers. This is a safety net, not a substitute.

Emit a new telemetry event `vesum_verified_negative_example_stripped` listing the per-statement skipped forms so we can audit how often the safety net fires. Goal: it should fire RARELY post-writer-prompt-fix; if it fires often, the writer prompt rule isn't being followed.

### 3. Add a writer-output validator (belt-and-suspenders)

In `scripts/build/linear_pipeline.py` after writer artifacts are written but BEFORE python_qg runs, add a soft check that scans for unmarkered non-VESUM Ukrainian forms in obvious teaching contexts:

```python
def detect_unmarkered_negative_examples(activities_yaml: str) -> list[dict]:
    """Find TF statements / non-error-correction items containing forms that
    match the `X, а не Y` pattern but lack <!-- bad --> markers.

    Returns a list of soft-warning dicts {activity_id, item_idx, form, hint}.
    Emits as `writer_negative_example_unmarkered` telemetry event but does
    NOT block the build — the gate will catch the real failures.
    """
```

This makes writer mistakes visible upstream so the next writer iteration can be tightened.

### 4. Tests — `tests/build/test_vesum_negative_example_handling.py`

Mandatory test cases (10 minimum):

1. **`<!-- bad -->` in TF statement is stripped** — pre-existing path; assert TF statement `"X — Y, а не <!-- bad -->Z<!-- /bad -->."` with `answer: true` does NOT trigger vesum lookup on `Z`.
2. **`<!-- bad -->` in error-correction `sentence:` is harmless** — assert no regression: error-correction sentence with markers behaves identically to without (since subtree is already skipped).
3. **TF statement `"X, а не Y."` without markers** — the safety net strips `Y` from VESUM lookup; emit `vesum_verified_negative_example_stripped` event.
4. **TF statement `"X, not Y."` (English mix, e.g. Pro-track)** — same safety-net behavior.
5. **TF statement with no negative-example pattern** — no safety-net stripping, no event emitted.
6. **TF statement with `answer: false`** — already not VESUM-checked (existing behavior); confirm no regression.
7. **Match activity with bad form in `left:`** — without markers, fails (gate behavior unchanged); with markers, passes.
8. **Fill-in activity with bad form in `sentence:`** — without markers, fails; with markers, passes.
9. **`detect_unmarkered_negative_examples` finds writer omissions** — synthesize an activities.yaml with one unmarkered "X, не Y" → assert one finding returned.
10. **End-to-end smoke**: build a synthetic activities.yaml + module.md mirroring m20's structure (with `act-error-l2` + the offending TF statement) — assert (a) without markers, gate fails on Y; (b) with the new safety-net code, gate passes AND emits the negative-example-stripped event.

### 5. Documentation update

In `docs/best-practices/vocabulary-activity-standards.md` (or wherever the marker convention is documented for human reading), add a short "Bad-form markers in YAML" section pointing at the writer-prompt rule + gate behavior.

---

## Verifiable claims (per #M-4)

| Claim | Tool + raw output |
|---|---|
| Writer prompt updated | `git diff origin/main -- scripts/build/phases/linear-write*.md` showing the new bad-marker section + anti-pattern callout |
| Gate-side helper added | `git diff origin/main -- scripts/build/linear_pipeline.py` showing the new `_TF_NEGATIVE_EXAMPLE_RE` + TF branch wiring |
| Validator added | same diff showing `detect_unmarkered_negative_examples` |
| New tests pass | `.venv/bin/pytest tests/build/test_vesum_negative_example_handling.py -v` final summary raw |
| Existing vesum / pipeline tests still pass | `.venv/bin/pytest tests/build/ tests/audit/ tests/test_linear_pipeline_wiki_coverage.py -q` final summary raw |
| Full pytest green | `.venv/bin/pytest tests/ -q` final summary raw (NO `-x` per #1942) |
| Ruff clean | `.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/build/phases/ tests/build/test_vesum_negative_example_handling.py` raw |
| Pre-commit clean | `.venv/bin/python -m pre_commit run --files <changed>` raw |
| m20 worktree replay** | Re-run vesum_verified gate against `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260518-000636/curriculum/l2-uk-en/a1/my-morning/` (read-only, no rebuild) and quote the new `vesum_verified` outcome. Should now PASS for the TF-statement `дивюся` while keeping all real `vesum_verified` failures (if any other words fail VESUM legitimately, they should still surface). |
| Commit + PR | `git log -1 --oneline` + `gh pr view --json url` raw |

**No claim allowed without its raw output line.** Per #M-4.

** For the m20 replay claim: invoke the gate function directly via a one-shot Python repl that re-reads the worktree's artifacts and re-calls `_vesum_gate(...)`. Don't rebuild the module — only re-run the gate. This is a deterministic test of whether the fix would have unblocked m20.

---

## Worktree setup

Branch: `fix/2128-vesum-bad-marker-everywhere`. Path: `.worktrees/dispatch/codex/2128-vesum-bad-marker-20260518-024000/`.

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/build/test_vesum_negative_example_handling.py -v
.venv/bin/pytest tests/build/ tests/audit/ -q
.venv/bin/pytest tests/ -q
.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/build/phases/ tests/build/
.venv/bin/python -m pre_commit run --files \
    scripts/build/linear_pipeline.py \
    scripts/build/phases/linear-write.md \
    tests/build/test_vesum_negative_example_handling.py
# m20 worktree replay (READ-ONLY — does NOT rebuild module).
# venv symlinked from main; run from worktree root
.venv/bin/python -c "
from pathlib import Path
import json, yaml
from scripts.build.linear_pipeline import _vesum_gate
mod_dir = Path('/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260518-000636/curriculum/l2-uk-en/a1/my-morning')
module_text = (mod_dir / 'module.md').read_text(encoding='utf-8')
activities = yaml.safe_load((mod_dir / 'activities.yaml').read_text(encoding='utf-8'))
vocabulary = yaml.safe_load((mod_dir / 'vocabulary.yaml').read_text(encoding='utf-8'))
resources = yaml.safe_load((mod_dir / 'resources.yaml').read_text(encoding='utf-8'))
result = _vesum_gate(module_text=module_text, activities=activities, vocabulary=vocabulary, resources=resources, verify_words_fn=None)
print(json.dumps({k: v for k, v in result.items() if k != 'missing'}, ensure_ascii=False, indent=2))
print('missing[:10]:', result.get('missing', [])[:10])
"
git diff --stat origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.
Per #1942: NO `-x` flag.

## Commit + PR

Conventional commit. Title: `fix(audit): vesum_verified handles negative-example forms in true-false statements (#2128)`. Body covers:
1. Root cause (writer convention gap)
2. Two-pronged fix (writer prompt + gate-side safety net)
3. m20 worktree replay outcome (quote the JSON output)
4. All verifiable-claims raw outputs

NO `--auto-merge`.

## Out of scope

- Don't change `_ERROR_CORRECTION_INTENTIONAL_FIELDS` — it already correctly includes `sentence`, the error-correction path is fine.
- Don't fix the OTHER m20 gate failures (`l2_exposure_floor` 13 vs 14, `inject_activity_ids` unused-4) — those are separate writer issues filed in #2128 §"original analysis" and may be writer-prompt fixes too, but each in a separate PR for reviewable scope.
- Don't add per-item `negative_examples: [...]` schema field — overkill for the current issue; the marker convention + safety net cover the cascade. If we hit cases the safety net can't handle, file a follow-up.
- Don't touch the wiki_coverage_gate / wiki_coverage_review code paths — separate concern.

## Anti-fabrication preamble

If anything in this brief surprises you when you read the code:

- `_ERROR_CORRECTION_INTENTIONAL_FIELDS` doesn't include `sentence` (it should — line 597 of linear_pipeline.py — if not, the m20 failure has a different cause and the gate-side fix needs reframing)
- `_strip_metalinguistic` doesn't already handle `<!-- bad -->...<!-- /bad -->` markers (it should — docstring at line 5866-5869)
- the writer prompt is in a different file than `scripts/build/phases/linear-write*.md`
- the TF activity walker behavior is different from what's described

STOP and quote the surprise verbatim before patching.

If the safety-net regex you write is too greedy and starts stripping legitimate VESUM forms, ABORT and fall back to writer-prompt-only fix. The whole point is to STOP false negatives on intentional bad forms while NOT introducing false positives that hide real writer errors.

## Notes for orchestrator (Claude, not Codex)

* This is the highest-cascade-risk tech debt currently open per the inventory check tonight. Fixing it unblocks every module with TF activities naming a contrast.
* Estimated duration: 30-45 min (medium scope: 2 prompts + 1 gate-side helper + 10 tests + 1 doc update).
* On finalize: verify m20 replay output is included in PR body — that's THE proof the fix works on the real failing case.
* AFTER merge: re-fire m20 v7_build to see if the architecture ships m20 E2E. If it does, file the OTHER m20 quality issues (#2128 §l2_exposure_floor / inject_activity_ids) as separate follow-ups for tomorrow.
