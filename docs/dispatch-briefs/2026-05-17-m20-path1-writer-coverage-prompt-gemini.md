# Dispatch brief — m20 Path 1: writer-coverage explicit-obligation prompt

> Surface: Gemini (gemini-3.0-flash-preview), unmetered. Fully-specified prompt-text edit, docs-near-code lane.
> Why: yesterday's 5-PR cascade closed every infrastructure gap; the residual problem is the writer dropping 14/18 wiki obligations silently. The `<implementation_map>` block at `scripts/build/phases/linear-write.md:20-28` already says "for each obligation_id... do not defer" but the writer treats that as suggestive, not load-bearing. Path 1 makes it load-bearing.

## Background — verifiable claims this work will produce

| Claim | Tool / evidence |
|---|---|
| File `scripts/build/phases/linear-write.md` modified at the specified lines | `git diff main scripts/build/phases/linear-write.md` raw output |
| `<implementation_map>` block updated with HARD REJECT wording | `sed -n '20,40p' scripts/build/phases/linear-write.md` raw output |
| Pre-emit count check added | `grep -n 'Count them\|count them\|N obligations' scripts/build/phases/linear-write.md` raw output |
| Pre-commit hooks pass | `git push` output (ruff, format, mypy if any) |
| PR opened | `gh pr view --json url` raw URL line |

No code logic change. No tests required (this is prompt-text-only). Per #M-4: every claim above is grounded in the listed tool output — quote the raw output in commit/PR body, not "I checked X."

## Worktree setup (mandatory — #M-7 + delegate-must-use-worktree rule)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/m20-path1-writer-coverage -b fix/m20-writer-explicit-obligation-coverage origin/main
cd .worktrees/m20-path1-writer-coverage
```

## The patch — exact edit

Target file: `scripts/build/phases/linear-write.md`

### Edit 1 — replace the current `<implementation_map>` block (lines 20-28) with the strengthened version

**OLD (lines 20-28 inclusive — match exactly, replace all):**

```
<implementation_map>
For each obligation_id in the Wiki Obligations Manifest, list:
  - obligation_id: <id>
  - artifact: <module.md | activities.yaml | vocabulary.yaml | resources.yaml>
  - location: <section name or activity id>
  - treatment: <how the obligation is addressed, for example "contrast_pair in activity act-3"
                or "prose explanation in section §Дієслова на -ся paragraph 2">
Do not defer. Every obligation must be implemented in THIS module, not a later one.
</implementation_map>
```

**NEW (replace the block above with this — same XML tag, expanded body):**

```
<implementation_map>
**MUST list ALL `obligation_id`s from the Wiki Obligations Manifest. No exceptions.**

The `<implementation_map>` blocks across your N section-`<plan_reasoning>` nodes, taken together, MUST mention every `obligation_id` in the manifest exactly once. Silent omission of any `obligation_id` is a HARD REJECT — the rebuild is wasted and the gate will fail with `implementation_map_missing`.

For each `obligation_id` in the Wiki Obligations Manifest, list:
  - obligation_id: <id>
  - artifact: <module.md | activities.yaml | vocabulary.yaml | resources.yaml>
  - location: <section name or activity id>
  - treatment: <how the obligation is addressed, for example "contrast_pair in activity act-3"
                or "prose explanation in section §Дієслова на -ся paragraph 2">

**Do not defer silently. Every obligation must be implemented in THIS module unless you explicitly mark it deferred.** If, after careful drafting, an obligation genuinely cannot fit within the four sections of this A1 module (e.g., it requires grammar not yet introduced), emit it anyway with:
  - artifact: <none>
  - location: <none>
  - treatment: `deferred (out of A1 scope) — <one-sentence justification>`

Explicit deferral is far better than silent omission: the gate sees an honest decision and the orchestrator can reassign the obligation. Silent omission is a HARD REJECT and forces a full rebuild.
</implementation_map>
```

### Edit 2 — add a pre-emit count check after line 48 (just before "## Tier-1 verification discipline")

**Find this exact line (currently line 48):**

```
Only after all `<plan_reasoning>` blocks are complete and passed may you emit the four fenced artifact blocks.
```

**REPLACE that single line with:**

```
Only after all `<plan_reasoning>` blocks are complete and passed may you emit the four fenced artifact blocks.

### Pre-emit obligation-count check (mandatory — #2094)

Before emitting the four artifact fences, you MUST audit your own `<implementation_map>` blocks against the Wiki Obligations Manifest:

1. Count the `obligation_id`s in the Wiki Obligations Manifest (call this `N`).
2. Count the distinct `obligation_id`s mentioned across all your `<implementation_map>` blocks (call this `M`).
3. If `M < N`, STOP. Go back, find the missing `obligation_id`s, and add them to the appropriate section's `<implementation_map>` — either with a real `treatment` or with the explicit `deferred (out of A1 scope)` escape hatch.
4. Only when `M == N` may you proceed to emit the four artifact fences.

Emit a single visible audit line BEFORE the artifact fences:

`<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[<list any IDs that ended up with treatment: deferred>]</implementation_map_audit>`

If this audit line is missing, or if `covered_in_map < manifest_obligations`, the writer has failed the protocol and the rebuild is wasted.
```

## Verification (do these and quote raw output)

In the worktree:

```bash
# venv symlinked into worktree by delegate.py
# 1. Confirm the implementation_map block changed and contains the HARD REJECT wording
sed -n '20,50p' scripts/build/phases/linear-write.md
grep -n 'HARD REJECT\|MUST list ALL\|deferred (out of A1 scope)' scripts/build/phases/linear-write.md

# 2. Confirm the pre-emit count check landed
grep -n 'Pre-emit obligation-count check\|implementation_map_audit\|manifest_obligations=' scripts/build/phases/linear-write.md

# 3. Check overall line delta (~30 LOC expected, not 200)
git diff --stat main

# 4. Make sure nothing else changed
git diff --name-only main
# Expected output: a single line `scripts/build/phases/linear-write.md`

# 5. Run pre-commit hooks
# venv symlinked into worktree by delegate.py
.venv/bin/python -m pre_commit run --files scripts/build/phases/linear-write.md
```

Quote each command's raw output in the PR body — don't paraphrase.

## Commit + PR

```bash
# venv symlinked into worktree by delegate.py
git add scripts/build/phases/linear-write.md
git commit -m "fix(writer): force explicit obligation coverage in implementation_map (#2094)

Yesterday's 5-PR cascade closed every wiki_coverage_gate infrastructure
bug. The residual issue is the writer dropping 14 of 18 manifest
obligations silently rather than listing them.

This patch:

1. Strengthens the <implementation_map> block to a HARD REJECT contract:
   the writer MUST list every obligation_id from the manifest in one of
   the section-level implementation_map blocks. Silent omission is now
   an explicit gate failure.

2. Adds an explicit deferral escape hatch (treatment: 'deferred (out of
   A1 scope) — <reason>') so a genuinely-out-of-scope obligation can be
   marked explicitly rather than silently dropped. The orchestrator can
   reassign deferred items; silent omissions force a full rebuild.

3. Adds a pre-emit count check: before emitting the four artifact
   fences, the writer must self-audit that count(obligation_ids in
   manifest) == count(distinct obligation_ids in implementation_maps).
   The audit line <implementation_map_audit> is emitted visibly.

Background: morning handoff
docs/session-state/2026-05-17-morning-m20-five-fixes-plus-dagger-cleanup.md
documented this as Path 1 (recommended). Best build of yesterday hit
22% coverage (4/18); target is >=80%.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Gemini <noreply@anthropic.com>"
git push -u origin fix/m20-writer-explicit-obligation-coverage
gh pr create --title "fix(writer): force explicit obligation coverage in implementation_map (#2094)" --body "$(cat <<'EOF'
## Summary

Yesterday's 5-PR cascade (#2087, #2088, #2090, #2091, #2092, #2093) closed every infrastructure bug around `wiki_coverage_gate`. The residual problem is the writer itself: best build of the day hit only **4/18 = 22% coverage**, and worst (#15) regressed to 2/18, because the writer treats the existing 'list each obligation' instruction as suggestive rather than load-bearing.

This patch implements **Path 1** from the morning handoff (`docs/session-state/2026-05-17-morning-m20-five-fixes-plus-dagger-cleanup.md` § "Recommended next step"): convert the `<implementation_map>` block into a hard contract with an explicit-deferral escape hatch and a pre-emit count check.

### Why not Path 2 (lower threshold) or Path 3 (per-obligation loop)

- Path 2 violates `memory/MEMORY.md` #1 ("no lowering thresholds") and the broader pedagogy principle that incomplete wiki coverage is incomplete teaching.
- Path 3 (per-obligation review loop) is the right answer eventually but is a Phase 2b-sized refactor; Path 1 is the surgical now-fix.

### What this changes

| File | Before | After |
|---|---|---|
| `scripts/build/phases/linear-write.md` | `<implementation_map>` block says "for each obligation" without enforcement; no count check | HARD REJECT wording for silent omission; explicit `treatment: deferred (out of A1 scope) — <reason>` escape hatch; pre-emit count audit emitting `<implementation_map_audit>` visible line |

Total prompt delta: ~30 LOC additions, no logic / no tests / no API surface change.

### Expected impact

# venv symlinked into worktree by delegate.py
Per morning handoff: ~50% odds of >=80% coverage in 1-2 m20 rebuilds. The next session will validate by re-running `.venv/bin/python -u scripts/build/v7_build.py a1 m20-cooking-and-meals --worktree` and checking `wiki_coverage_gate` output for `covered_pct >= 0.8`.

### Verification

(Quote raw output from `sed -n '20,50p'`, `grep -n 'HARD REJECT'`, `git diff --stat`, `pre_commit run` — see brief.)

## Test plan

- [x] Pre-commit hooks pass on the changed file
- [ ] Next-session test: rebuild m20-cooking-and-meals and check `wiki_coverage_gate` output (>=80% target)
- [ ] If coverage <80% after 2 rebuilds, escalate to Path 3 (per-obligation review loop)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## NO auto-merge

Open the PR and stop. The orchestrator will merge after a quick diff review.

## Out-of-scope (do NOT do)

- ❌ Do not rebuild m20. The orchestrator will run that after this PR merges.
- ❌ Do not touch `scripts/audit/wiki_coverage_gate.py` (yesterday's #2093 already fixed the parser side).
- ❌ Do not lower any threshold in `scripts/config.py` or `scripts/audit/config.py`.
- ❌ Do not add or modify tests in `tests/test_wiki_coverage_gate.py` — this patch is prompt-text-only.
- ❌ Do not change any file other than `scripts/build/phases/linear-write.md`. A diff with more than one file modified is a sign of scope creep — back out and re-do.

## Anti-fabrication reminders (#M-4)

- Quote `sed`, `grep`, `git diff`, `pre_commit run`, and `gh pr view` raw output in the PR body. Don't paraphrase.
- If any step fails (pre-commit, push, PR creation), STOP and report the literal error message + the command that produced it. Don't retry blindly.
- If the patch text above doesn't apply cleanly (e.g., line numbers shifted because someone else edited the file), STOP. Don't manually rewrite — escalate to the orchestrator who can rebase the brief.
