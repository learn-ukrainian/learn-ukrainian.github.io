# Codex dispatch brief — pipeline gate trio (vesum sentence-exclusion + textbook_grounding parser + immersion display)

> **Issues:** none yet — file 3 issues during/after fix (one per gate).
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/pipeline-gate-trio-2026-05-13/`
> **Base:** `origin/main` (currently `e7e892bb7a`)
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Every command that uses `.venv/`, `scripts/`, or files in MAIN checkout MUST be prefixed with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/pipeline-gate-trio-2026-05-13 && ...` or absolute path.

Inside the worktree, `.venv/` is gitignored. Use MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Fix 3 pipeline gate bugs that block `a1/my-morning` publication. The three are independent on the surface but bundle naturally — all live in `scripts/build/linear_pipeline.py` gate logic and were named as followups in the 2026-05-13 afternoon handoff (`docs/session-state/2026-05-13-afternoon-bakeoff-and-twopass-brief.md` § "Still-open pipeline followups", items 1, 2, 4).

After this fix, re-running `python_qg` on `audit/bakeoff-2026-05-13-midday/claude/` should show:
- `vesum_verified.passed = true` (3 currently-missing forms accepted via sentence-level exclusion)
- `textbook_grounding.passed = true` (3 currently-missing textbook hits matched via MCP markdown parser)
- `immersion.max_pct` reflects actual policy cap (24%, not 35%) for `a1-m15-24` policy lookup

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "vesum sentence-level exclusion now applied" | `grep -n 'sentence' scripts/build/linear_pipeline.py` shows new exclusion clause near existing `errorWord` / `error_word` handling | quote the grep output |
| "textbook_grounding parser reads MCP markdown" | run `.venv/bin/python -c "<reproduce gate on claude bakeoff>"` shows `textbook_result_hits ≥ 1` | quote `python_qg.json` diff before/after |
| "immersion display fixed" | re-run python_qg on claude bakeoff; `immersion.max_pct` now equals the policy cap (24 for `a1-m15-24`), not the prior hardcoded 35 | quote the `immersion` block |
| "Tests pass" | `.venv/bin/pytest tests/test_linear_pipeline*.py tests/test_*_gate*.py` | quote final summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py` | quote final line |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## The three bugs — exact evidence

### Bug A: vesum_verified sentence-level exclusion gap

**Evidence from `audit/bakeoff-2026-05-13-midday/claude/python_qg.json` `vesum_verified` gate:**
```json
{
  "passed": false,
  "checked": 193,
  "whitelisted": 6,
  "missing": ["діал", "йдуся", "снідаюся"],
  "missing_count": 3
}
```

- `діал` is the abbreviation `діал.` for `діалектне` used in error-correction didactic prose. Appears in a teaching-note sentence labeling a form as dialectal.
- `йдуся`, `снідаюся` are intentionally-wrong forms in error-correction activities. The activity structure presents them in a `sentence:` field as the "what learner must FIX" reference. Per the activity schema, the correct form lives in another field; the wrong one is required content but should NOT be VESUM-checked.

Current code excludes `error:` / `errorWord:` / `error_word:` fields but NOT `sentence:` when the sentence belongs to an error-correction activity. Sister fields exist; sister field for `sentence` in this context (within an error-correction activity) must be added to the exclusion set.

**Find the gate:** `grep -n 'errorWord\|error_word\|whitelisted' scripts/build/linear_pipeline.py` to locate. Activity schema reference: `claude_extensions/schemas/activity-*.yaml` or `scripts/build/track_constraints.py`.

**Fix shape:** when an activity has `type` in the error-correction family (verify exact type names from existing test fixtures or schema), exclude lemmas appearing in its `sentence` field from the VESUM check.

**Test it:** add a fixture in `tests/test_*_gate*.py` (or wherever `vesum_verified` is tested) with an error-correction activity whose `sentence` field contains a deliberately-wrong form — assert `passed=true` and the wrong form NOT in `missing`.

### Bug B: textbook_grounding HARD parser bug

**Evidence from same `python_qg.json` `textbook_grounding` gate:**
```json
{
  "passed": false,
  "verdict": "REJECT",
  "severity": "HARD",
  "required": 1,
  "matched": [],
  "missing": ["Караман Grade 10, p.176", "Кравцова Grade 4, p.113", "Захарійчук Grade 4, p.162"],
  "blockquotes_checked": 6,
  "long_blockquotes_checked": 5,
  "search_text_calls": 5,
  "textbook_result_hits": 0
}
```

The writer called `mcp__sources__search_text` 5 times AND got results — verifiable in `audit/bakeoff-2026-05-13-midday/claude/writer_tool_calls.json`. But `textbook_result_hits: 0`. The gate's `_is_textbook_result()` (or whatever the parser is called) doesn't recognize the MCP-formatted markdown response.

**Find the parser:** `grep -n '_is_textbook_result\|textbook_result_hits\|search_text' scripts/build/linear_pipeline.py`. Look for the function that classifies whether a tool-call result counts as a textbook hit.

**Today's MCP response format** (verify by calling `mcp__sources__search_text` yourself with a simple query OR by reading the result blobs in `audit/bakeoff-2026-05-13-midday/claude/writer_tool_calls.json`):
The result is formatted markdown text like:
```
### Result 1 - Source: Grade X, author / Text: ...
```

The gate parser is presumably looking for structured fields (`source_type='textbook'` or similar). Teach it to ALSO recognize the markdown-formatted shape — parse the `Source:` line, extract `Grade X, author` and `p.Y`, normalize, match against the `missing` list.

**Test it:** add a fixture in the textbook_grounding test suite with a tool-call result in MCP markdown format → assert `textbook_result_hits ≥ 1` and `passed=true` when the source matches.

### Bug C: immersion display vs policy

**Evidence:**
```json
"immersion": {
  "passed": false,
  "pct": 25.4,
  "min_pct": 15,
  "max_pct": 35,        // ← WRONG: policy a1-m15-24 caps at 24, not 35
  "policy": "a1-m15-24",
  ...
}
```

`max_pct: 35` is hardcoded somewhere but `policy: a1-m15-24` literally encodes the cap as 24 in its name. The display field should derive from the policy, not from a stale default.

**Find:** `grep -n 'max_pct\|min_pct\|a1-m15-24\|immersion' scripts/build/linear_pipeline.py` and `grep -rn 'a1-m15-24' scripts/`. Policy probably lives in `scripts/build/track_constraints.py` or a yaml.

**Fix shape:** parse the policy name (or look it up in the policy registry) and emit `max_pct` from the actual policy value, not a hardcoded fallback. If policy parsing is fragile, prefer: policy registry lookup with a clear error if not found.

**Test it:** assert that for `a1-m15-24`, `max_pct == 24`. Same for other policies — verify the existing list of immersion policies has correct min/max.

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/pipeline-gate-trio-2026-05-13 .worktrees/dispatch/codex/pipeline-gate-trio-2026-05-13 origin/main
   ```
2. **File-level work** — fix Bugs A, B, C in `scripts/build/linear_pipeline.py` (+ schema/policy files if needed). Aim for minimal surface; each fix should be 5-30 LOC.
3. **Test suite** — for each bug, add a focused test. Then run:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/pipeline-gate-trio-2026-05-13 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_linear_pipeline*.py tests/test_*gate*.py -x
   ```
   Quote final summary line.
4. **Ruff:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build/linear_pipeline.py
   ```
   Quote final line.
5. **Regression check** — re-run python_qg on the claude bakeoff artifact (copy or symlink `audit/bakeoff-2026-05-13-midday/claude/` into the worktree if needed, OR write a small driver that calls the gate functions directly on those files). Capture before/after gate JSON for each of the three bugs in the PR body.
6. **Commit** — one commit per bug is clean, or one combined commit if changes are tightly coupled. Conventional message: `fix(linear_pipeline): vesum sentence-exclusion + textbook_grounding parser + immersion policy-derived cap`.
7. **Push:** `git push -u origin codex/pipeline-gate-trio-2026-05-13`.
8. **Open PR** via `gh pr create`. Body must include:
   - Before/after `python_qg` snippets for each of the three gates
   - Confirmation that `claude/python_qg.json` would now show `passed=true` for vesum_verified, textbook_grounding, and correct `immersion.max_pct`
   - File 3 separate GH issues for tracking (one per bug, each closed by this PR), OR open one combined issue — pick one approach and stick to it
9. **DO NOT auto-merge.** Hand back for review.

---

## What blocks the merge

- Any of the three gates not actually passing on the claude bakeoff artifact post-fix.
- Tests failing.
- Ruff failing.
- A behavior change to other gates (e.g. accidentally relaxing word_count, surzhyk, etc.).

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json` or `audit/*-review.md` files in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] Every changed file directly related to the three gate fixes
- [ ] Total files changed < 20

---

## Related

- Predecessor handoff: `docs/session-state/2026-05-13-afternoon-bakeoff-and-twopass-brief.md`
- Discussion that confirmed pipeline-side issues block A1 publication: channel `twopass-workflow-2026-05-13`
- Bakeoff artifacts: `audit/bakeoff-2026-05-13-midday/`
