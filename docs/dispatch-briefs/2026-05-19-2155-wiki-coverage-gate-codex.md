# Dispatch Brief — #2155 wiki_coverage_gate absence-required bans (Codex)

**Date:** 2026-05-19
**Issue:** [#2155](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2155) — `[gate] wiki_coverage_gate misclassifies absence-required decolonization_bans as substance-required (m20 build #8: 3 false-failures)`
**Target agent:** Codex (gate semantics + classifier heuristic + tests — Codex's lane)
**Mode:** `danger`
**Worktree:** mandatory
**Auth note:** Codex re-login completed 2026-05-19 evening (rotated JWT). The agent_runtime PTY+stdin large-prompt crash documented at #2159 does NOT apply here — this dispatch operates on small focused files, not 200K-char V7 writer prompts.

---

## Background

m20 build #8 (post-γ shipped in PR #2153) ran with the seeded `implementation_map.json` contract rendered into the writer prompt. **Wiki coverage jumped from 22% → 67%** vs build #7. The gate reports 6 of 18 obligations failing — but diagnostic replay shows **3 of those 6 are gate-side false-failures**, not writer gaps.

Under the corrected gate semantics, build #8 would be at **~83% (15/18)** — above the 80% min_pct hard gate threshold, would have shipped on wiki_coverage_gate. Every future module with absence-required bans hits the same false-failure pattern.

## The bug

`scripts/audit/wiki_coverage_gate.py::_check_obligation_text` (lines 523-527) evaluates ALL `decolonization_ban` obligations with the same substance-presence check:

```python
if obligation_type == "decolonization_ban":
    rule = str(obligation.get("rule") or "")
    if _claim_markers_present(rule, target_text):
        return "PASS", "ban_substance_present"
    return "FAIL", "ban_substance_missing"
```

This expects the literal `rule` prose to appear in the module. For **absence-required bans** (pedagogical prohibitions like "Don't compare -ться to Russian -тся"), the rule text describes *what NOT to do* — by construction the rule itself should NOT appear in the module. The check produces a false `FAIL`.

The m20 manifest is the canonical demonstration:

| ID | Subtype | Rule shape | Current verdict |
|---|---|---|---|
| ban-1 | **absence-required** | Pure prose prohibition: "Don't use Russian explanations when teaching reflexive verbs" | ❌ false-FAIL |
| ban-2 | **absence-required** | Pure prose prohibition: "Don't compare -ться to Russian -тся" | ❌ false-FAIL |
| ban-3 | **absence-required** | Pure prose prohibition: "Don't claim -ся is borrowed/shared from Russian" | ❌ false-FAIL |
| ban-4 | **substance-required** | Contains explicit lexical pairs in prose: `«рушник» (не «полотенце»)`, `«сніданок» (не «завтрак»)`, `«одягатися» (не «одіватися»)`, `«Мені N років» / «Я маю N років» (калька)` | ✅ correctly checked |

Raw data: `audit/2026-05-19-m20-build-8-gamma-results/implementation_map.json` (entries for ban-1 through ban-4) and `audit/2026-05-19-m20-build-8-gamma-results/python_qg.json` (fix_proposals list with 3 false-failures).

---

## Job

Land a SINGLE PR closing #2155 with the following sequence:

### A. Add a ban subtype classifier

In `scripts/build/phases/implementation_map.py` (or a new helper module if the file is getting unwieldy), add a function that classifies each `decolonization_ban` obligation as `substance_required` or `absence_required` based on inspection of the `rule` text.

**Heuristic** (recommended; refine if you find a better signal):

A ban is `substance_required` if its rule contains at least one lexical-pair pattern. Detect any of:
- Cyrillic-quote substitution: `«WORD» (не «OTHER»)` or `«WORD»/«OTHER»`
- Calque marker: `«WORD»` paired with explicit `(калька)` or `(русизм)` or `(суржик)` markers
- Explicit substitution: word + `замість` + word (substitution preposition)

Otherwise the ban is `absence_required` (pure pedagogical prohibition prose, no extractable lexical pairs).

Use Cyrillic guillemets `«»` (U+00AB, U+00BB) as the primary quote delimiter — that's what the m20 ban-4 manifest uses. Don't depend on ASCII quotes; the manifest is Ukrainian-native.

**Tests** (`tests/build/test_implementation_map.py`):

- `test_classify_ban_substance_required_with_substitution_pairs` — feed ban-4 from m20 (the literal rule string), assert `substance_required`.
- `test_classify_ban_absence_required_pure_prohibition` — feed ban-1, ban-2, ban-3 from m20, assert `absence_required` for each.
- `test_classify_ban_edge_case_empty_rule` — feed a ban with `rule=""`, assert `absence_required` (default safe).
- `test_classify_ban_edge_case_mixed_prose_and_pair` — feed a ban with a prohibition prose + one pair: should still classify as `substance_required` because there's substance to check.

### B. Expose the classification on the obligation object

Either:
1. Add a `subtype` field on the obligation dict during `validate_obligations` (line 113 of `wiki_coverage_gate.py`), populated by the new classifier; OR
2. Add `subtype` during `seed_implementation_map` (`scripts/build/phases/implementation_map.py:113`) so it's stamped into the seeded contract and visible in `implementation_map.json` for downstream inspection.

Option 2 is preferred (decision visible in the audit artifact, classifier runs once per build instead of every gate call) but Option 1 is acceptable if cleaner. Use your judgment; either choice should have tests.

### C. Dispatch on subtype in the gate

In `scripts/audit/wiki_coverage_gate.py::_check_obligation_text` (line 523), replace the current uniform `decolonization_ban` block with subtype-aware logic:

```python
if obligation_type == "decolonization_ban":
    subtype = str(obligation.get("subtype") or "substance_required")  # default = legacy behavior
    if subtype == "substance_required":
        rule = str(obligation.get("rule") or "")
        if _claim_markers_present(rule, target_text):
            return "PASS", "ban_substance_present"
        return "FAIL", "ban_substance_missing"
    # absence_required: gate cannot affirmatively verify absence of arbitrary
    # patterns described in pedagogical prose, so PASS by default. A writer
    # who violates an absence directive is caught by other gates (russianisms_clean,
    # check_russian_shadow, etc.) — that's the right separation of concerns.
    return "PASS", "absence_obligation_assumed_satisfied"
```

**Tests** (`tests/audit/test_wiki_coverage_gate.py` — extend existing or add new file):

- `test_decolonization_ban_substance_required_passes_when_pair_present` — minimal manifest with ban-4-style rule + module containing the lexical pairs → PASS.
- `test_decolonization_ban_substance_required_fails_when_pair_missing` — same manifest, module missing the pairs → FAIL with reason `ban_substance_missing`.
- `test_decolonization_ban_absence_required_passes_automatically` — minimal manifest with ban-1-style rule + arbitrary module text → PASS with reason `absence_obligation_assumed_satisfied`.
- `test_decolonization_ban_legacy_manifest_without_subtype_field` — ban without `subtype` field set → default to `substance_required` (backward compatibility).

### D. Replay build #8 to verify the fix end-to-end

Use the captured forensics in `audit/2026-05-19-m20-build-8-gamma-results/`:

```bash
# Symlink .venv into the worktree (worktrees don't inherit the main project venv)
ln -s /Users/krisztiankoos/projects/learn-ukrainian/.venv .venv 2>/dev/null || true
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from scripts.audit.wiki_coverage_gate import check_wiki_coverage_paths

forensics = Path("audit/2026-05-19-m20-build-8-gamma-results")
# You'll need to find/reconstruct the m20 build output dir; if it's not in
# the forensics dir, use the seeded contract + the manifest from the m20
# plan (curriculum/l2-uk-en/a1/plans/m20-*.md → wiki_obligations section).
# Goal: show that under the fix, ban-1/2/3 PASS (absence_obligation_assumed_satisfied)
# and ban-4 keeps its current verdict (whatever it was — substance check applies).
result = check_wiki_coverage_paths(...)  # exact args depend on what forensics covers
print(json.dumps(result, indent=2, ensure_ascii=False))
PY
```

Capture the before/after coverage_pct + obligation list in the PR body. The headline number is: **before fix m20 reported 67% (12/18 PASS); after fix m20 reports ≥83% (15/18 PASS)**. If you find a different number, document why.

### E. Standard PR closeout

- Branch: `fix/2155-wiki-coverage-gate-absence-bans`
- Commits: split if useful (classifier + tests, gate dispatch + tests, replay docs)
- Conventional commit messages per repo style
- `X-Agent: codex-gpt55` trailer per AGENTS.md
- PR title: `fix(gate): wiki_coverage_gate dispatches decolonization_ban by subtype (substance vs absence) — closes #2155`
- PR body MUST include the "What this PR does" + "Verifiable claims" sections per the verifiable-claims preamble below.
- Do NOT auto-merge.

---

## Verifiable claims preamble (per #M-4 — Deterministic Over Hallucination)

| Claim | Deterministic tool | Output format in PR body |
|---|---|---|
| Classifier function exists and is tested | `.venv/bin/pytest tests/build/test_implementation_map.py -k classify_ban -v` | Raw `passed` summary line |
| Gate subtype-dispatch works | `.venv/bin/pytest tests/audit/test_wiki_coverage_gate.py -k decolonization_ban -v` | Raw `passed` summary line |
| Full test suite green | `.venv/bin/pytest tests/build tests/audit` (no `-x` — run all, see #1942) | Raw `N passed in M.MMs` line |
| Ruff clean | `.venv/bin/ruff check scripts/audit scripts/build tests` | Raw `All checks passed!` line |
| m20 replay shows 3 false-failures resolved | Replay script in §D | Coverage % before vs after + per-obligation verdict for ban-1/2/3 |
| ban-4 verdict unchanged | Same replay, focus on ban-4 row | ban-4 status before == status after |
| Pre-commit passed | `git commit` output | `✅ pre-commit passed` literal line |

**"I checked X" without one of the above artifacts in the PR body is a hard fail.** The orchestrator will reject the PR and ask you to re-run with evidence.

---

## Halt / escalate triggers

| Trigger | Action |
|---|---|
| Classifier heuristic ambiguous for >5% of inspected bans in the wider corpus | Halt, write status to orchestrator. Either refine heuristic with a clearer signal or add a `subtype` field to the manifest source and let the wiki authors hand-tag. |
| Replay can't reproduce the 67% → 83% jump | Halt, investigate the forensics shape. Possible the m20 build output drifted since 2026-05-19; in that case use the captured `python_qg.json` + a synthetic minimal-manifest replay to demonstrate the fix on the 4 ban entries specifically. |
| Tests reveal a deeper bug in `_check_obligation_text` (e.g., `_claim_markers_present` incorrectly matches partial prose) | File a follow-up issue, do NOT expand scope — this PR fixes the dispatch, not the substring matching. |
| A test fails after pre-commit's auto-fix (whitespace/EOF) | Re-stage, re-commit. Do NOT bypass hooks. |
| You hit any blocker requiring user input | Use `ab ask-claude` (orchestrator session) or write status to `docs/session-state/` — DO NOT push a partial PR. |

---

## Out of scope (do NOT touch in this PR)

- The bigger wiki-obligation-emission-contract refactor (decision card `docs/decisions/2026-05-18-wiki-obligation-emission-contract.md`). This PR is a narrow gate-semantics fix; the contract redesign is a separate workstream.
- Russian-shadow detection upgrades. If absence-required bans need stricter enforcement, file a follow-up.
- Other gate failures (l2_exposure_floor, inject_activity_ids) — separate work referenced in #2155.
- Manifest source-of-truth changes (the wiki obligations sections in plan files). Classifier should infer from existing data, not require manifest authoring changes.

---

## Refs

- Issue: [#2155](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2155)
- γ shipped: PR #2153 (`5ac671a1b5`)
- Decision card: `docs/decisions/2026-05-18-wiki-obligation-emission-contract.md` §Risks #2
- Path 3 architecture: `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`
- Forensics: `audit/2026-05-19-m20-build-8-gamma-results/`
- Original architectural gap: #2148 (substantially closed by γ)
- Codex runner caveat (#2159): NOT applicable to this dispatch — small focused prompts only
