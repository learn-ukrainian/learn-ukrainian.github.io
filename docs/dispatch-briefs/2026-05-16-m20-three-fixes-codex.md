# Dispatch brief — m20 GREEN: three small fixes (issue #2032)

**Task ID**: `m20-three-fixes-2026-05-16`
**Agent**: Codex (gpt-5.5, high effort)
**Mode**: `danger` with `--worktree`
**Base**: `main` (currently `d6066a64cd`)
**Expected runtime**: ~15-25 min
**Owner**: Claude orchestrator

---

## Why this work

m20 build #9 reached 19/22 substantive gates GREEN (best to date). Three content/structural gates remain RED, all with concrete fix paths in #2032. Total scope: ~25 LOC + 2 tests + 1 YAML edit. Ship as one PR.

## #M-4 verifiable-claims contract (read before starting)

For every claim this work produces, the PR body MUST quote the deterministic tool output that backs it:

| Claim you will assert | Deterministic tool | Required output to quote |
|---|---|---|
| "Fix 1 regex added to `_strip_metalinguistic`" | `git diff scripts/build/linear_pipeline.py` | Show the diff hunk including the new regex constant and its use in the function |
| "Fix 1 test passes" | `.venv/bin/python -m pytest tests/build/test_linear_pipeline.py::<your-test-name> -v` | Raw pytest line `1 passed in N.Ns` |
| "Fix 2 corpus citation is real" | `mcp__sources__search_text` against the new source/page | Quote the chunk returned + cite chunk_id |
| "Fix 3 anchor-unmatched no longer leaks" | New regression test in `tests/build/test_linear_pipeline.py` | Raw pytest pass line |
| "Full pytest does not regress" | `.venv/bin/python -m pytest tests/build/test_linear_pipeline.py -q` | Raw final summary line `N passed in M.MMs` |
| "Lint clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py` | `All checks passed!` line |
| "PR opened" | `gh pr view <num> --json url --jq .url` | Raw URL line |

No "I verified X" without the matching command + raw output in the PR body. Vibes-claims are forbidden per `docs/best-practices/deterministic-over-hallucination.md`.

---

## Step 1 — Worktree setup

```
git fetch origin
git worktree add -B codex/m20-three-fixes-2026-05-16 \
    .worktrees/dispatch/codex/m20-three-fixes-2026-05-16 origin/main
cd .worktrees/dispatch/codex/m20-three-fixes-2026-05-16
.venv/bin/python -m pytest tests/build/test_linear_pipeline.py -q   # baseline must be GREEN; if RED, STOP and report
```

---

## Step 2 — Fix 1: warning-quote strip in `_strip_metalinguistic`

**Location**: `scripts/build/linear_pipeline.py:4917` (function `_strip_metalinguistic`).

**Symptom**: m20 writer's prose pattern `... grow an epenthetic л in the я-form (дивитися → я дивлюся, not "дивюся") ...` causes `дивюся` to flow into VESUM lookup as if it were a real lemma. The wrong form is in quotes prefixed by `not` — the canonical negative-example pattern.

**Fix**: Add a new regex constant near the other `_*_RE` constants (look at where `_AVOID_MARKER_RE` is defined for the pattern), and apply it inside `_strip_metalinguistic` like the other strips:

```python
# Near the other _*_RE constants:
_WARNING_QUOTE_RE = re.compile(r'\bnot\s+["«][^"»]+["»]', re.IGNORECASE)
```

```python
# Inside _strip_metalinguistic, alongside the other text = _X_RE.sub(...) lines:
text = _WARNING_QUOTE_RE.sub(" ", text)
```

**Why this exact pattern**: Matches `not "X"` (ASCII quotes) AND `not «X»` (Ukrainian guillemets). Case-insensitive on `not`. The handoff brief's prescribed regex (`r'\bnot\s+["«][^"»]+["»]'`) is the spec.

**Test** (add to `tests/build/test_linear_pipeline.py`): a `test_strip_metalinguistic_warning_quote_pattern` case that asserts both:
- `_strip_metalinguistic('я дивлюся, not "дивюся"')` does NOT contain `дивюся`
- `_strip_metalinguistic('кажуть, not «дивюся»')` does NOT contain `дивюся`
- A legitimate quote that ISN'T preceded by `not` is preserved (e.g. `the word "ранок" means morning` → still contains `ранок`)

Update the function's docstring (lines 4917-4944) to mention the new strip class.

---

## Step 3 — Fix 2: reviewer-anchor-leak in the gate's `missing` list

**Symptom** (from #2032): the codex-tools dim-reviewer's `<fixes>` block proposed `find: двоколонкова, replace: двоколонна`. The text actually contains `двоколонна` (correct), so the `find` doesn't anchor. Event `reviewer_fixes_anchor_unmatched anchor_preview=двоколонкова text_preview=двоколонна` fires (this part works — see `scripts/build/linear_pipeline.py:3770-3800`). BUT the bogus anchor `двоколонкова` then leaks into the `vesum_verified` gate's `missing` list as if the writer had emitted it.

**Where the leak happens**: NOT in the event-emit site at line ~3770 (that's correct). Look for where the gate assembles its `missing` list — somewhere downstream of `_apply_reviewer_fixes` that consumes fix anchors into VESUM-lookup tokens. Likely candidates: `_vesum_gate`, `_collect_vesum_targets`, or wherever fix-anchors get fed into the VESUM extractor.

**Fix**: when a fix anchor failed to match (i.e. the `reviewer_fixes_anchor_unmatched` codepath fired), do NOT include the failed anchor in any downstream VESUM-token list. Track unmatched anchors in a set during `_apply_reviewer_fixes` and exclude them from the missing-list assembly.

**Test**: regression test in `tests/build/test_linear_pipeline.py` that constructs a small text + fixes pair where one `find` doesn't anchor; assert the unmatched anchor string does NOT appear in the downstream `missing` list of the resulting gate output.

If the leak path is NOT obvious after 15-20 min of grepping, STOP and emit a `GOAL_ABORT`-style status with the candidate functions you inspected and a one-line summary of why each didn't seem to be the leak. Don't ship a speculative "fix" that doesn't isolate the root cause.

---

## Step 4 — Fix 3: m20 plan citations (Захарійчук Grade 4 → A1-appropriate)

**Location**: `curriculum/l2-uk-en/plans/a1/my-morning.yaml` lines 32-33 (in `plan_overview.references` array) and lines 84-87 (in `references` array).

**Symptom**: cites Захарійчук Grade 4 pages 162-163. Grade 4 Захарійчук is NOT in the corpus per #1901; only Grade 1 is. PR #2014 supposedly fixed but re-introduced wrong pages.

**Fix process (MANDATORY MCP grounding, do NOT pick pages from memory)**:

1. Run `mcp__sources__search_text` for `-ся verbs` and `dressing/washing morning routine` queries against the corpus, filtered to A1-level / Grade 1 Захарійчук sources.
2. Identify 1-2 chunks that actually cover -ся conjugation for A1 morning-routine vocab (вмиватися, одягатися, прокидатися).
3. Replace lines 32-33 (plan_overview.references) and 84-87 (references) with the new citation, including the real `chunk_id`s returned by MCP.
4. Update the `notes:` field of each new reference to accurately describe what the corpus chunk says (paraphrase only — never quote verbatim per CLAUDE.md "we have so many content").

If NO appropriate Grade 1 chunk is found, do NOT invent one. STOP and emit `GOAL_ABORT` with `last_cmd` = the MCP search command you ran, `last_output` = the empty/insufficient result, and `next_action` = "user must extend corpus or downgrade textbook_grounding to ADVISORY".

PR body MUST quote the MCP chunk returned (or the empty result) as proof.

---

## Step 5 — Verify

```
.venv/bin/python -m pytest tests/build/test_linear_pipeline.py -q     # both new tests + no regression
.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py curriculum/l2-uk-en/plans/a1/my-morning.yaml
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/plans/a1/my-morning.yaml || true    # informational
```

YAML lint may flag formatting; only fix if the existing file would also have flagged. Do not reformat unrelated YAML.

---

## Step 6 — Commit

Single commit, conventional message:

```
git add scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py curriculum/l2-uk-en/plans/a1/my-morning.yaml
git commit -m "$(cat <<'EOF'
fix(m20): three gate fixes for vesum_verified + textbook_grounding

Closes #2032 prerequisites for m20 GREEN:

1. _strip_metalinguistic: new _WARNING_QUOTE_RE handles `not "X"` /
   `not «X»` prose-quoted negative examples (removes false-positive
   on дивюся from m20 build #9).

2. _apply_reviewer_fixes: track unmatched find-anchors and exclude
   them from downstream VESUM missing-list assembly (removes false-
   positive on двоколонкова from the codex-tools dim-reviewer's
   hallucinated <fixes> anchor).

3. a1/my-morning.yaml plan: swap Захарійчук Grade 4 pages 162/163
   (not in corpus per #1901) for A1-appropriate Grade 1 / corpus-
   verified chunks via mcp__sources__search_text grounding.

Refs #2032

Co-Authored-By: <agent-attribution>
EOF
)"
```

---

## Step 7 — Push and open PR

```
git push -u origin codex/m20-three-fixes-2026-05-16
gh pr create --title "fix(m20): three gate fixes for vesum_verified + textbook_grounding (closes #2032)" --body "$(cat <<'EOF'
## Summary

Three small fixes from #2032 to take m20 from 19/22 to 22/22 substantive gates green.

[Quote the raw verification outputs per the #M-4 contract — pytest summary lines, MCP search chunks, etc.]

## Test plan

- [x] New test `test_strip_metalinguistic_warning_quote_pattern` passes
- [x] New test for anchor-unmatched leak passes
- [x] Full `tests/build/test_linear_pipeline.py` suite stays green
- [x] `ruff check` clean on touched files
- [ ] **NOT in this PR** — m20 V7 build re-run (orchestrator will do that after merge, with --worktree, monitor JSONL stream)

Refs #2032

🤖 Generated with [Claude Code](https://claude.com/claude-code) via Codex dispatch
EOF
)"
```

---

## Step 8 — NO auto-merge

Open the PR. **Do not merge.** Orchestrator reviews + merges after the run, and re-runs the m20 build.

`AGENT_NO_MERGE=1` is already set by the delegate runtime; do not override.

---

## Status-line schema for `/goal` style turns (if you use it)

```
GOAL_STATUS turn=N/M blocked=N/M no_progress=N/M queue_head=<fix1|fix2|fix3|verify|commit|push|pr>
GOAL_DONE reason="PR <url> opened, all 3 fixes verified by raw outputs in PR body"
GOAL_ABORT reason="<why>" last_cmd="..." last_cwd="..." last_output="..." next_action="..."
```

Abort cleanly if Fix 2's leak path can't be isolated; partial PR with Fixes 1 + 3 + a note on Fix 2's investigation is acceptable (better than a speculative leak fix).
