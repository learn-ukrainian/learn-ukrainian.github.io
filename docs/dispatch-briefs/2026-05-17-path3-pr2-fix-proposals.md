# Dispatch brief — Path 3 PR2: `wiki_coverage_gate` emits structured `<fix_proposals>` on failure

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952, enforced by `delegate.py dispatch`)
**Scope:** PR2 of 4 in Path 3 architecture per
`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` line 138.
Gate extension only — emits `fix_proposals` when failing. NO reviewer wiring
(that is PR3). NO pipeline behavior change beyond surfacing the new field
in the existing JSONL event stream.

---

## Why

Decision Card line 64:

> Per Codex: gate already verifies per-obligation. Extend output to report
> **structured `<fix_proposals>`** when failing — each failure has
> `obligation_id`, `current_artifact_state`, `expected_treatment`,
> `surgical_diff_hint`. This is the input the Phase 3 reviewer consumes.

PR1 (merged in `0f96f459f4`, PR #2108) wrote the deterministic
`implementation_map.json` sidecar with per-entry `treatment_template` and
verbatim `manifest_payload`. PR2 connects that sidecar to the gate so when
the writer's filled-in artifacts fail validation, the gate can emit a
structured fix proposal per failed obligation that PR3's batched reviewer
will consume.

PR2 is gated logic only — no LLM calls, no reviewer wiring, no plumbing to
`_apply_writer_correction`. The gate's existing return shape gains one new
key (`fix_proposals`) when `passed=False`; existing callers keep working.

---

## What you build

### 1. Extend `scripts/audit/wiki_coverage_gate.py`

#### 1a. New kwarg on `check_wiki_coverage` / `check_wiki_coverage_paths`

```python
def check_wiki_coverage(
    *,
    manifest: Mapping[str, Any],
    implementation_map: Mapping[str, Mapping[str, str]] | str,
    module_md: str,
    activities_yaml: str,
    vocabulary_yaml: str = "",
    resources_yaml: str = "",
    level: str | None = None,
    seeded_map: Mapping[str, Any] | None = None,   # NEW
) -> dict[str, Any]:
    ...
```

`seeded_map` is the parsed `implementation_map.json` sidecar shape produced
by PR1's `seed_implementation_map`. When `None`, the gate behaves exactly
as today (back-compat: tests that don't pass `seeded_map` get no
`fix_proposals` field).

When `seeded_map` is provided AND the gate fails, the gate must emit a
`fix_proposals` key on its return dict (see §1c).

For `check_wiki_coverage_paths`, look for `module_dir / "implementation_map.json"`:
- If it exists → parse via `scripts.build.phases.implementation_map.read_implementation_map` and pass as `seeded_map`.
- If absent → pass `seeded_map=None` (back-compat for old modules built before PR1).

#### 1b. New helper: build a single fix proposal per failed obligation

```python
def _build_fix_proposal(
    obligation_result: Mapping[str, Any],
    seeded_entry: Mapping[str, Any] | None,
    artifacts: Mapping[str, str],
) -> dict[str, Any]:
    """Return a structured fix proposal for ONE failed obligation.

    Schema:
        {
            "obligation_id": "<from obligation_result>",
            "obligation_type": "<from obligation_result>",
            "failure_reason": "<from obligation_result.reason>",
            "current_artifact_state": "<snippet or 'MISSING'>",
            "expected_treatment": <dict from seeded_entry.treatment_template or {}>,
            "surgical_diff_hint": "<one-line natural-language guidance>",
            "manifest_payload": <verbatim from seeded_entry, or {} if no sidecar>,
        }
    """
```

#### 1c. Wire fix_proposals into `check_wiki_coverage` return

After the existing `obligation_results` loop completes, when `passed=False`:

```python
seeded_index = (
    {entry["obligation_id"]: entry for entry in (seeded_map.get("entries") or [])}
    if seeded_map else {}
)
fix_proposals = [
    _build_fix_proposal(
        result,
        seeded_index.get(str(result["obligation_id"])),
        artifacts,
    )
    for result in obligation_results
    if result["status"] == "FAIL"
]
```

Add `"fix_proposals": fix_proposals` to the return dict. When `passed=True`,
do NOT add the key (avoid noise in the success event).

#### 1d. `surgical_diff_hint` mapping (deterministic, per failure reason)

| `failure_reason` (from `_check_obligation_text`) | `surgical_diff_hint` template |
|---|---|
| `implementation_map_missing` | `f"Add <implementation_map> entry: obligation_id={oid}; artifact={seed.artifact}; location={seed.location_hint}; treatment={seed.obligation_type}"` |
| `unknown_artifact` | `f"Writer claimed artifact={claim.artifact}, but obligation requires artifact={seed.artifact}"` |
| `claimed_location_missing` | `f"Location '{claim.location}' returns empty text in {claim.artifact}. Verify the section heading or activities.yaml block exists (expected: {seed.location_hint})"` |
| `missing_incorrect` | `f"Insert manifest_payload.incorrect ({payload.incorrect!r}) verbatim into the activities.yaml entry at {claim.location}"` |
| `missing_correct` | `f"Insert manifest_payload.correct ({payload.correct!r}) verbatim"` |
| `missing_incorrect_and_correct` | both lines joined by `; ` |
| `contrast_pair_not_in_activity` | `f"Move contrast_pair to activities.yaml entry — currently claimed in {claim.artifact}"` |
| `prose_substance_missing` | `f"Add prose paragraph naming manifest_payload.correct ({payload.correct!r}) and explaining manifest_payload.why ({payload.why!r})"` |
| `phonetic_rule_missing` | `f"Add prose stating written={payload.written!r} → spoken={payload.spoken!r} with at least one example pair"` |
| `sequence_claim_missing` | `f"Add section heading or step marker matching manifest_payload.heading ({payload.heading!r}); required_claim: {payload.required_claim!r}"` |
| `ban_substance_missing` | `f"Remove phrasing matching manifest_payload.rule ({payload.rule!r}) — negative obligation: absence required"` |
| `unknown_obligation_type` | `f"Unknown obligation type {result.type!r} — seeder bug, file follow-up"` |

When `seeded_entry is None` (sidecar wasn't passed in), use `obligation_result.claim` fallback values and emit a degraded hint that says `"(no seeded sidecar — hint reduced; PR3 reviewer should run with --seeded-map)"`. Do NOT raise.

#### 1e. `current_artifact_state` derivation

For each failed obligation:

1. If `failure_reason == "implementation_map_missing"` → `"MISSING (no <implementation_map> entry from writer)"`
2. If `failure_reason == "unknown_artifact"` or `"claimed_location_missing"` → quote the writer's `claim` dict as `f"writer_claim={claim!r}; resolved_artifact_text=''"`
3. Otherwise → return a snippet of `evidence_text` (the actual artifact section the gate examined), truncated to 400 chars with ellipsis. Do NOT include the full module.md — keep snippets bounded.

The 400-char cap keeps the gate's return value JSON-serializable at reasonable size when 18+ obligations fail.

### 2. Pipeline wiring (LIGHT — pass-through + event emit)

In `scripts/build/linear_pipeline.py::run_wiki_coverage_gate`, the existing
function already calls `check_wiki_coverage_paths(module_dir=...)`. The
sidecar load is in PR2's new `check_wiki_coverage_paths` body (§1a), so the
pipeline call signature does NOT change.

What DOES change: after the gate returns, when `passed=False`, emit a JSONL
event with the new field:

```python
{
  "event": "wiki_coverage_fix_proposals",
  "slug": <slug>,
  "fail_count": len(result["fix_proposals"]),
  "proposals": result["fix_proposals"],   # full list
}
```

This event becomes the input PR3's reviewer pipeline consumes. PR3 will
gate on its presence — do NOT consume it yet in PR2.

Find the existing emission of the gate result in `linear_pipeline.py` (search
for the event tag `wiki_coverage` or the `run_wiki_coverage_gate` call site)
and add the new event right after. Do NOT replace the existing event.

If no existing event is emitted today, add `wiki_coverage_fix_proposals`
immediately after the `run_wiki_coverage_gate` call and before the
`return`/`raise` for the failure path. Match the JSONL emit style of the
seeder event in PR1 (`implementation_map_seeded`).

### 3. Tests: `tests/audit/test_wiki_coverage_gate_fix_proposals.py`

Mandatory test cases (12 minimum):

1. **PASS short-circuit**: when `passed=True`, return dict has NO
   `fix_proposals` key.
2. **Back-compat**: omitting `seeded_map` kwarg (or passing `None`) still
   produces `fix_proposals` on failure (degraded hints OK), so existing
   callers that haven't been updated keep failing visibly.
3. **`implementation_map_missing`**: writer-emitted implementation_map omits
   one obligation → fix proposal includes the seeded `artifact` and
   `location_hint`.
4. **`unknown_artifact`**: writer claims `artifact="readme.md"` → fix
   proposal surfaces the seeded `artifact` as the correction target.
5. **`claimed_location_missing`**: writer claims `location="§Diaspora"`
   but no such heading exists → fix proposal quotes the writer's claim
   AND the seeded `location_hint`.
6. **`missing_incorrect`**: contrast_pair activity is missing the
   `incorrect` marker → fix proposal mentions `payload.incorrect`
   verbatim.
7. **`missing_correct`**: contrast_pair activity is missing the `correct`
   marker → same shape with `payload.correct`.
8. **`missing_incorrect_and_correct`**: both missing → hint joins both
   lines with `"; "`.
9. **`contrast_pair_not_in_activity`**: writer placed contrast_pair in
   `module.md` not `activities.yaml` → hint says to move it; quotes the
   claim's artifact.
10. **`prose_substance_missing`**: l2_error prose_explanation lacks both
    `correct` and `why` → fix proposal quotes both payload fields.
11. **`phonetic_rule_missing`**: missing written/spoken contrast → hint
    quotes both payload fields, mentions example pairs.
12. **`sequence_claim_missing`** AND **`ban_substance_missing`**: each
    produces a proposal that names the seeded payload field
    (`heading`/`required_claim` for sequence; `rule` for ban).
13. **`current_artifact_state` truncation**: a 2000-char `evidence_text`
    is truncated to 400 chars + ellipsis.
14. **JSON-serializability**: a fix_proposals list with 18 entries
    serializes via `json.dumps(result, sort_keys=True)` without
    raising.
15. **m20 real-world**: load m20's actual manifest + the build's last
    writer output if available (or synthesize a writer output that
    omits 10 of the 18 obligations) → assert `len(fix_proposals) == 10`
    and each proposal has all 7 schema keys non-empty (except
    `manifest_payload` may be `{}` if sidecar absent).

For test fixtures: reuse the same manifest fixture pattern PR1 used in
`tests/build/test_implementation_map.py`. Add a small "writer output"
fixture string per failure case — multi-line YAML-shaped is fine.

### 4. Docstring updates

Update the module docstring at the top of `wiki_coverage_gate.py` to
mention the new optional `seeded_map` flow and the `fix_proposals` return
key. Reference the Decision Card path so future maintainers can find the
why.

---

## Verifiable claims this PR must produce (per #M-4)

| Claim | Tool + raw output to quote in PR body |
|---|---|
| Gate extended in place | `git diff --stat origin/main` showing `scripts/audit/wiki_coverage_gate.py` row |
| New test file landed | same diff showing `tests/audit/test_wiki_coverage_gate_fix_proposals.py` row |
| New tests pass | `.venv/bin/pytest tests/audit/test_wiki_coverage_gate_fix_proposals.py -v` final summary line raw |
| Existing gate tests still pass | `.venv/bin/pytest tests/test_wiki_coverage_gate.py -q` final summary line raw |
| Full audit + build tests still green | `.venv/bin/pytest tests/audit/ tests/build/ -q` final summary line raw (NO `-x` per #1942) |
| Ruff clean | `.venv/bin/ruff check scripts/audit/wiki_coverage_gate.py tests/audit/test_wiki_coverage_gate_fix_proposals.py scripts/build/linear_pipeline.py` raw output |
| m20 real-world gate produces ≥1 fix_proposal | one-shot: `.venv/bin/python -c "from pathlib import Path; from scripts.audit.wiki_coverage_gate import check_wiki_coverage_paths; from scripts.build.phases.implementation_map import read_implementation_map; mp = read_implementation_map(Path('docs/path3-test-m20/implementation_map.json')) if Path('docs/path3-test-m20/implementation_map.json').exists() else None; r = check_wiki_coverage_paths(manifest='wiki/pedagogy/a1/my-morning.md', implementation_map='', module_dir=Path('curriculum/l2-uk-en/a1/m20-my-morning'), seeded_map=mp); print(f'passed={r[\"passed\"]} fix_proposals={len(r.get(\"fix_proposals\", []))}')"` raw output (gracefully degrade if m20 dir doesn't exist) |
| Pipeline JSONL event added | `git diff scripts/build/linear_pipeline.py` showing the `wiki_coverage_fix_proposals` emit |
| Commit landed + PR opened | `git log -1 --oneline` raw + `gh pr view --json url` raw URL |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

`delegate.py dispatch --worktree` handles the worktree creation. The
canonical shape is:

```bash
.worktrees/dispatch/codex/path3-pr2-fix-proposals-<timestamp>/
```

Branch name: `feat/path3-pr2-fix-proposals`.

---

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked into worktree by delegate.py
.venv/bin/pytest tests/audit/test_wiki_coverage_gate_fix_proposals.py -v
.venv/bin/pytest tests/test_wiki_coverage_gate.py -q
.venv/bin/pytest tests/audit/ tests/build/ -q
.venv/bin/ruff check scripts/audit/wiki_coverage_gate.py \
                    tests/audit/test_wiki_coverage_gate_fix_proposals.py \
                    scripts/build/linear_pipeline.py
# venv symlinked from main; run from worktree root
.venv/bin/python -m pre_commit run --files \
    scripts/audit/wiki_coverage_gate.py \
    tests/audit/test_wiki_coverage_gate_fix_proposals.py \
    scripts/build/linear_pipeline.py
git diff --stat origin/main
git diff --name-only origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.
Per #1942: NO `-x` flag.

---

## Commit + PR

```bash
git add scripts/audit/wiki_coverage_gate.py \
        tests/audit/test_wiki_coverage_gate_fix_proposals.py \
        scripts/build/linear_pipeline.py
git commit -m "$(cat <<'EOF'
feat(audit): Path 3 PR2 — wiki_coverage_gate emits structured fix_proposals

Decision Card docs/decisions/2026-05-17-path3-per-obligation-review-loop.md
line 64: extend wiki_coverage_gate output to report structured
<fix_proposals> when failing — each failure has obligation_id,
current_artifact_state, expected_treatment, surgical_diff_hint. This is
the input the Phase 3 batched reviewer (PR3) will consume.

PR2 scope (this PR):
* New optional kwarg seeded_map: Mapping[str, Any] | None on
  check_wiki_coverage. When provided AND gate fails, return dict gains
  fix_proposals: list[dict].
* check_wiki_coverage_paths reads module_dir/implementation_map.json
  (PR1's sidecar) when present; passes through as seeded_map. Absent =
  back-compat with degraded hints, no raise.
* _build_fix_proposal helper produces one entry per failed obligation
  with deterministic surgical_diff_hint per failure_reason (11 reasons
  mapped per brief table). current_artifact_state truncated to 400 chars.
* linear_pipeline emits new JSONL event wiki_coverage_fix_proposals
  with the full list when gate fails. PR3 consumes; PR2 does not wire
  reviewer.
* 15 contract tests covering: PASS short-circuit (no field),
  back-compat (no sidecar OK), each of the 11 failure reasons, 400-char
  truncation, JSON-serializability of 18-entry lists, m20 real-world
  smoke.

Out of scope:
* PR3 batched reviewer routing + max-iter cap + _apply_writer_correction
  wiring.
* PR4 Phase 5 Goodhart sentinel.
* Any change to writer prompt or PR1's seeder behavior.

Verification:
* tests/audit/test_wiki_coverage_gate_fix_proposals.py: <quote pytest final line>
* tests/test_wiki_coverage_gate.py existing tests: <quote pytest final line>
* tests/audit/ + tests/build/ full: <quote pytest final line>
* ruff: <quote raw>
* m20 real-world fix_proposals count: <quote stdout>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Codex <noreply@anthropic.com>
EOF
)"
git push -u origin feat/path3-pr2-fix-proposals
gh pr create --title "feat(audit): Path 3 PR2 — wiki_coverage_gate emits structured fix_proposals on failure" --body "$(cat <<'EOF'
## Summary

Second of 4 Path 3 PRs per Decision Card
`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`.

Extends `scripts/audit/wiki_coverage_gate.py` so that when the gate fails,
its return dict gains a structured `fix_proposals` field. Each proposal
entry carries:

* `obligation_id`, `obligation_type`, `failure_reason`
* `current_artifact_state` (snippet of what the gate saw, truncated to 400 chars)
* `expected_treatment` (from PR1's seeded `implementation_map.json` `treatment_template`)
* `surgical_diff_hint` (one-line natural-language guidance — deterministic per failure_reason)
* `manifest_payload` (verbatim from seeded sidecar)

Pipeline emits a new JSONL event `wiki_coverage_fix_proposals` with the
full list when the gate fails. PR3 will consume this as the input to the
batched reviewer correction loop. PR2 itself adds NO reviewer wiring and
NO behavior change beyond surfacing the new field.

Back-compat: callers that don't pass `seeded_map` still get
`fix_proposals` with degraded hints (no raise). `check_wiki_coverage_paths`
auto-loads `module_dir/implementation_map.json` when present.

## Verifiable claims (per #M-4)

* Gate + tests + pipeline updated: <quote git diff --stat>
* `tests/audit/test_wiki_coverage_gate_fix_proposals.py`: <quote pytest final line raw>
* `tests/test_wiki_coverage_gate.py` (existing): <quote pytest final line raw>
* Full `tests/audit/ tests/build/`: <quote pytest final line raw>
* `ruff check`: <quote raw "All checks passed!" line>
* m20 real-world fix_proposals count: <quote stdout>

## Test plan

* [x] PASS short-circuit (no `fix_proposals` key when gate passes)
* [x] Back-compat (no `seeded_map` kwarg → degraded hints OK)
* [x] Each of 11 failure reasons → correct surgical_diff_hint template
* [x] 400-char truncation on `current_artifact_state`
* [x] JSON-serializability on 18-entry list
* [x] m20 real-world smoke

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

NO `--auto-merge`. Leave the PR open; orchestrator merges after review.

---

## Out of scope (do NOT include)

* PR3 reviewer wiring, max-iter cap, `_apply_writer_correction` plumbing.
* PR4 Goodhart sentinel (Gemini cross-family pass).
* Any change to PR1's seeder (`scripts/build/phases/implementation_map.py`)
  beyond importing `read_implementation_map`. If you find a seeder bug,
  STOP and file a follow-up issue — don't paper it over inside PR2.
* Any change to writer prompt or `_apply_writer_correction`.
* External_resources obligations (`validate_obligations` excludes them today;
  PR2 must mirror the same scope — fix_proposals only for the 4 obligation
  groups the gate already validates).
* Cosmetic refactors to `_check_obligation_text` or `_build_fix_proposal`
  internals beyond what's needed for the proposal logic. Keep the diff
  focused.

---

## Anti-fabrication preamble

If anything in this brief surprises you — the gate's return shape is
different from what's described, PR1's sidecar schema doesn't have
`treatment_template` per entry, `_check_obligation_text` returns failure
reasons not listed in the table above, the m20 module dir doesn't exist —
STOP and quote the surprise verbatim before patching. Don't paper over.

If `_check_obligation_text` includes failure reasons beyond the 11 listed
above by the time you read this, ADD a row to the surgical_diff_hint
mapping (don't fail-soft). Quote the new reason in the PR description so
future maintainers know the mapping is exhaustive at PR2-merge time.

If a test feels redundant or impossible to write deterministically, name
the specific test and the specific blocker — do not silently drop tests
from the list.

If a failure reason has no useful `manifest_payload` field to quote (e.g.
`unknown_obligation_type` indicates a seeder bug, not a writer fix),
emit the proposal with `manifest_payload={}` and a `surgical_diff_hint`
that says "file follow-up issue — seeder bug". Don't suppress the entry.

## Notes for orchestrator (Claude, not Codex)

* Dispatch CAP currently 1 Codex used (#2001 OCR quality filter, started
  T+72s at orient time). Firing PR2 takes us to 2/2 Codex slots — still
  within cap, but no headroom for another Codex dispatch until one lands.
* Monitor pattern per #M-8: schedule a 1200s (20 min) wakeup to poll
  `/api/delegate/active`. PR2 is mechanical-with-design-judgment; estimated
  duration 15–25 min based on PR1's 560s.
* On PR2 finalize: read the PR body, verify the 6 verifiable-claims raw
  outputs are quoted, check CI rollup, merge if all blocking checks green,
  delete the worktree + branch via the same hygiene flow as the late-night
  session.
