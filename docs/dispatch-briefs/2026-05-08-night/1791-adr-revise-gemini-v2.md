# Dispatch brief v2: revise #1791 Decision Graph ADR (fixes Claude review's 4 IMPORTANT)

> **PR to revise:** #1791 on branch `gemini/decision-graph-adr` (existing remote branch)
> **Origin review:** `gh pr view 1791 --json comments` (Claude headless adversarial review)
> **Verdict:** REVISE [OBJECT]
> **Agent:** Gemini (drafting + revisions, original author)
> **Worktree:** NEW worktree, branched from existing PR tip; force-push back.

## Worktree instructions (mandatory — note the --base)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent gemini --mode danger --worktree --base origin/gemini/decision-graph-adr \
    --task-id gemini-1791-adr-fix \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1791-adr-revise-gemini-v2.md
```

After making fixes locally, **push back to the ORIGINAL PR branch**:

```bash
git push origin HEAD:gemini/decision-graph-adr --force-with-lease
```

Then DELETE the new branch from origin:

```bash
git push origin --delete gemini/1791-adr-fix
```

PR #1791 picks up the amendments automatically.

## Issues to fix

### Issue 1 (IMPORTANT) — Fabricated `ADR-008` cross-reference

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:7`

Frontmatter says `independent of Multi-UI ADR (ADR-008)`. **Reality:** ADR-008 is `docs/decisions/2026-05-05-adr-008-supersession-resolved-keep.md` (Phase-5 pipeline correction, NOT Multi-UI). The Multi-UI ADR is `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`.

**Fix**: replace `(ADR-008)` parenthetical with explicit file path: `independent of docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`. **Verify by reading both files first.**

### Issue 2 (IMPORTANT) — Missing `Scope:` frontmatter field

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:1-7`

`docs/decisions/pending/README.md:31` requires `Scope:` for pending decisions. Without it, orchestrator can't reason about blocking scope.

**Fix**: add to frontmatter:
```
Scope: Decision Graph view in channels.html — UI toggle, marker parser, matrix layout, drawer; not the underlying DB schema or `ab discuss` broker logic.
```

### Issue 3 (IMPORTANT) — Q3 marker parsing too vague

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:78-83`

Q3 says "fuzzy matching using a regex boundary" but provides no actual regex.

**Fix**: replace "fuzzy matching" prose with concrete regex:
```regex
\[(AGREE(?:D)?|OPTION|OBJECT(?:[^\]]*)?|DEFER)(?:\b[^\]]*)?\]
```
(case-insensitive). Add a short test-fixture table showing input → captured → maps-to.

### Issue 4 (IMPORTANT) — Body-size data over-generalizes

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:26-29, 70-71`

Body-size data is architecture-channel only. Pipeline avg=758 / max=4614, reviews avg=1673 / max=9654 (Claude verified).

**Fix** (pick one): (A) acknowledge variance in Q2 rationale ("matrix layout justified for high-density channels; lighter channels could fall back to body-first or use the same matrix as a uniform UX choice"); OR (B) expand the data table to include all channels and re-justify.

Prefer (A) for brevity.

### Issue 5 (NIT) — Q4 convergence wording muddled

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:91-94`

**Fix**: flatten to single rule:
```markdown
A thread is converged when every distinct `agent_family` that has posted in the thread emits `[AGREE]` in the latest round. Earlier-round content does not factor in.

Edge case (partial participation): if an agent posted earlier but is silent in the latest round, that agent is still considered "participating" — the thread is NOT converged until that agent re-posts with `[AGREE]` or another marker. To exit, an agent must explicitly emit `[DEFER]`.
```

## Acceptance criteria

1. `ADR-008` parenthetical replaced with proper file path (Issue 1)
2. `Scope:` frontmatter field present (Issue 2)
3. Q3 has concrete regex + test-fixture table (Issue 3)
4. Body-size rationale acknowledges variance OR includes cross-channel data (Issue 4)
5. Q4 flattened to single rule with partial-participation edge case (Issue 5)
6. **Status remains PROPOSED** — only user can flip to ACCEPTED
7. ADR-008 path verified by reading both files

## Numbered execution steps

1. `git worktree add` — handled by delegate runner.
2. Read the Claude review on PR #1791 in full.
3. Read both ADR files referenced in Issue 1 to verify the correct path.
4. Read `docs/decisions/pending/README.md` for `Scope:` field convention.
5. Apply fixes in order (Issue 1 → 5).
6. Verify markdown validity.
7. Commit: `docs(adr): revise decision-graph-view ADR per Claude review (Issues 1-5, [OBJECT] resolved)`
8. **Push to ORIGINAL PR branch**: `git push origin HEAD:gemini/decision-graph-adr --force-with-lease`
9. **Delete new branch**: `git push origin --delete gemini/1791-adr-fix`
10. Comment on PR #1791: `gh pr comment 1791 --body "Revised per Claude review: Issues 1, 2, 3, 4, 5 fixed. Status remains PROPOSED — awaiting user signoff."`
11. **Do NOT auto-merge.** **Status remains PROPOSED.**

## Out of scope

- Don't change the toggle-not-inversion conclusion (data supports it)
- Don't change Q1 auto-engage thresholds
- Don't change Q2 layout proposal beyond the rationale fix
- Don't change Q5 / Q6
- Don't restructure the frontmatter beyond Issues 1+2

## Why the v2 brief

The v1 brief failed at worktree-prep due to branch-name mismatch with the existing worktree. v2 uses `--base origin/gemini/decision-graph-adr` to branch a NEW worktree from the existing PR's tip, then force-pushes back. Supported topology.
