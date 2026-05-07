# Dispatch brief: revise #1791 Decision Graph ADR (Claude review found 4 IMPORTANT issues)

> **PR to revise:** #1791 (in-flight, branch `gemini/decision-graph-adr`)
> **Origin review:** PR comment by Claude headless on 2026-05-08 — full text on the PR
> **Verdict:** REVISE [OBJECT]
> **Agent:** Gemini (drafting + small revisions, original author)
> **Worktree:** existing at `.worktrees/dispatch/gemini/decision-graph-adr`

## Worktree instructions (continue existing worktree)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent gemini --mode danger --worktree .worktrees/dispatch/gemini/decision-graph-adr \
    --task-id gemini-1791-adr-revise \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1791-adr-revise-gemini.md
```

Push amendments to the same branch — PR #1791 picks them up automatically.

## Context

You wrote the original Decision Graph ADR draft. Claude headless adversarial review (xhigh) found 4 IMPORTANT issues + 3 NITs. **The data claims hold up** (Claude re-derived them from the live DB and verified — minor drift due to snapshot date, all directionally correct). The remaining gaps are factual errors, frontmatter omissions, vague specifications, and over-generalized rationale.

## What to fix (in order, all required)

### Issue 1 — Fabricated `ADR-008` cross-reference

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:7`

**Problem**: Frontmatter says: `independent of Multi-UI ADR (ADR-008)`. **Reality:** ADR-008 is `docs/decisions/2026-05-05-adr-008-supersession-resolved-keep.md` (Phase-5 pipeline correction architecture). It is NOT the Multi-UI ADR. The Multi-UI ADR is `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`.

**Fix**: Replace with explicit file path: `independent of docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`. Verify this is correct by reading both files.

### Issue 2 — Missing `Scope:` frontmatter field

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:1-7`

**Problem**: `docs/decisions/pending/README.md:31` says: *"Pending decisions block only the work declared in their `Scope` field, not all repository work."* The Multi-UI ADR has it. This ADR has none. Without `Scope:`, the orchestrator cannot reason about what work this PROPOSED card blocks.

**Fix**: Add this line to frontmatter:
```
Scope: Decision Graph view in channels.html — UI toggle, marker parser, matrix layout, drawer; not the underlying DB schema or `ab discuss` broker logic.
```

### Issue 3 — Q3 marker parsing too vague

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:78-83`

**Problem**: Q3 says "fuzzy matching using a regex boundary" but provides no actual regex. An implementer reading this will guess. Need a concrete regex.

**Fix**: Replace the "fuzzy matching" prose with a concrete, copy-paste-ready regex. Suggested:

```regex
\[(AGREE(?:D)?|OPTION|OBJECT(?:[^\]]*)?|DEFER)(?:\b[^\]]*)?\]
```

(case-insensitive flag). This matches `[AGREE]`, `[AGREED]`, `[OPTION]`, `[OBJECT]`, `[OBJECT - reason]`, `[DEFER]`, etc. Cite the rationale in the ADR (each variant maps to which canonical marker).

Optionally add a short test-fixture table:

| Input | Captures | Maps to |
|---|---|---|
| `... [AGREE]` | `AGREE` | AGREE |
| `... [AGREED]` | `AGREED` | AGREE |
| `... [OBJECT - missing context]` | `OBJECT` | OBJECT |
| `... [option]` (lowercase) | `option` | OPTION (case-i flag) |

### Issue 4 — Body-size data is architecture-only; ADR over-generalizes

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:26-29, 70-71`

**Problem**: "Codex's data shows average reply bodies are 2367 chars and max out at 8349 chars" — this is **architecture channel only**. Claude's re-run for other channels: pipeline avg=758 / max=4614, reviews avg=1673 / max=9654.

The Q2 rationale "body-first grid would stretch rows to unreadable heights" is true on `architecture` but does NOT hold on `pipeline` (758 chars ≈ 3-4 lines at 200 char/line).

**Fix**: Either (pick one):
- **(A) acknowledge the variance**: rewrite Q2 rationale to say "matrix layout justified for high-density channels (architecture); lighter channels could fall back to body-first or use the same matrix as a uniform UX choice." Note this in Open Questions if it should be a configurable choice.
- **(B) expand the data table** to include all channels and re-justify with the cross-channel data.

Prefer (A) for brevity.

### Issue 5 — Q4 convergence wording internally muddled

**File**: `docs/decisions/pending/2026-05-09-decision-graph-view.md:91-94`

**Problem**: Bullets sit at same indentation level so they read as additive rules, but the closing sentence ("strictly by terminal round") effectively negates bullet 2.

**Fix**: Flatten to a single rule:

```markdown
A thread is converged when every distinct `agent_family` that has posted in the thread emits `[AGREE]` in the latest round. Earlier-round content does not factor in.

Edge case (partial participation): if an agent posted earlier in the thread but is silent in the latest round, that agent is still considered "participating" — the thread is NOT converged until that agent re-posts with `[AGREE]` or another marker. To exit a thread, an agent must explicitly emit `[DEFER]`.
```

The added partial-participation rule resolves the case Claude flagged: "What about an agent who silently drops out of round 3 after `[AGREE]`-ing in round 2 — converged or not?"

### Issues 6 + 7 (NITs, optional)

- **Issue 6 (drawer filter)**: open-question already partly captures this; no required action.
- **Issue 7 (`[OPTION]` canonical?)**: grep `docs/best-practices/agent-cooperation.md` for `\[OPTION\]` — confirm or note non-canonical and propose adding to the canonical list.

## Acceptance criteria

1. `ADR-008` parenthetical replaced with proper file path (Issue 1)
2. `Scope:` frontmatter field present (Issue 2)
3. Q3 has concrete regex + test-fixture table (Issue 3)
4. Body-size rationale either acknowledges variance OR includes cross-channel data (Issue 4)
5. Q4 flattened to single rule with partial-participation edge case explicit (Issue 5)
6. Status remains **PROPOSED** (only user can flip)
7. Length not artificially padded — current 152 lines + ~50 net new lines from these fixes is fine
8. Verify the ADR-008 path you cite by reading both files first

## Numbered execution steps

1. Re-enter worktree (delegate runner via `--worktree .worktrees/dispatch/gemini/decision-graph-adr`).
2. Pull latest: `git fetch origin gemini/decision-graph-adr && git reset --hard origin/gemini/decision-graph-adr`.
3. Read the Claude review on PR #1791 in full: `gh pr view 1791 --json comments` (or via gh comment list).
4. Read both ADR files referenced in Issue 1 to verify the correct path.
5. Read `docs/decisions/pending/README.md` for `Scope:` field convention.
6. Read `docs/best-practices/agent-cooperation.md` for `[OPTION]` canonical-marker check (Issue 7).
7. Apply fixes in order (Issue 1 → 5).
8. Verify the ADR file is still valid markdown.
9. Commit: `docs(adr): revise decision-graph-view ADR per Claude review (Issues 1-5, [OBJECT] resolved)`
10. `git push origin gemini/decision-graph-adr` (force-push if rebased; otherwise plain push for new commit).
11. Add a comment to PR #1791 noting which Claude review issues were fixed: `gh pr comment 1791 --body "Revised per Claude review: Issues 1, 2, 3, 4, 5 fixed. Issue 6 partly addressed via Open Questions. Issue 7 verified."`
12. **Do NOT auto-merge.** **Status remains PROPOSED.** User flips to ACCEPTED.

## Out of scope

- Don't change the toggle-not-inversion conclusion (data supports it)
- Don't change Q1 auto-engage thresholds
- Don't restructure the frontmatter beyond adding `Scope:` and fixing the fabricated reference
- Don't add length for length's sake — the 152→200 lines target is fine if substance is added per fixes 3-5

## Why this matters

The ADR has the right shape and verified data. These 5 surgical fixes resolve the substantive issues that prevent user signoff. After this revision, the ADR should be ready for user review and ACCEPT.
