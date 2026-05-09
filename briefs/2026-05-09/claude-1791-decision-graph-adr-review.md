# Claude Headless (Opus 4.7, xhigh) — Adversarial review of #1791 Decision Graph ADR

## TL;DR

PR #1791 (`docs(adr): Decision Graph view ADR (PROPOSED, kubedojo Action C)`) has been **stale since 2026-05-08**. Only review on file is a `gemini-code-assist` drive-by suggesting refinements. CI is all green/skipped (docs-only paths). Awaits user signoff to flip PROPOSED → ACCEPTED.

The orchestrator (Claude main session) wants a **proper adversarial review** before pushing REVISE or recommending close. You are that review. **Read-only mode.** Output a verdict + concrete revision list OR a recommendation to close-as-superseded.

---

## What this work is

The ADR drafts the **Decision Graph view** — a matrix-based visualization of multi-agent deliberations, per Action C from `docs/session-state/2026-05-07-kubedojo-paradigm-followups.md`. It is a *view* / UI artifact tied to the channels + `ab discuss` infrastructure.

Branch: `gemini/decision-graph-adr`. PR: <https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/1791>.

## Mandatory orientation (#M-4 — deterministic over hallucination)

Before forming any opinion, read these via tool calls (no opining from priors):

1. **`docs/best-practices/deterministic-over-hallucination.md`** — top-priority rule. Every claim in your review must cite a file/line or quoted output. No "I think the design is weak" — only "Section X line N says Y, but conflict with file Z line M which says W."
2. **The PR diff** — `gh pr diff 1791` — read the entire ADR.
3. **`docs/session-state/2026-05-07-kubedojo-paradigm-followups.md`** — original framing of Action C.
4. **The Gemini code-assist review on the PR** — `gh pr view 1791 --json reviews` — its concrete findings (broaden auto-engagement criteria; unique agent identifiers; high-risk-track override; side-drawer UX; historical-thread logic).
5. **`docs/best-practices/agent-cooperation.md`** — multi-agent deliberation protocol context.
6. **`docs/best-practices/agent-bridge.md`** — channels + `ab discuss` (the underlying mechanism the view describes).
7. **Existing ADRs** — `ls docs/architecture/adr/` — internalize the project's ADR style.

## Your deliverable

A single review document at `audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md` (you'll write it inside your worktree). Per `#M-2`, MD is correct here (ai → ai output). The file MUST contain:

### Section 1 — Verdict

One of:
- **APPROVE-AS-PROPOSED** — ADR is sound, ship as PROPOSED, user can flip to ACCEPTED on signoff.
- **REVISE** — concrete list of revisions required before merge. Each revision = one bullet + line reference + reasoning.
- **REJECT** — fundamental flaw; recommend close + new ADR. Justify with at least 2 file/line citations.
- **SUPERSEDE** — argue that another open issue / ADR already covers this, link it, recommend close.

### Section 2 — Per-finding verification of the gemini-code-assist review

For each of Gemini's findings (auto-engagement / unique IDs / high-risk override / side-drawer / historical thread), verify against the ADR text and respond:
- **Confirmed valid** + your concurrence with the suggested fix
- **Partially valid** + your refinement
- **Invalid** + your reasoning citing the ADR text

### Section 3 — Independent findings

Gaps Gemini missed. Examples to look for: ADR template compliance (Status / Context / Decision / Consequences sections), terminology consistency with channels.html and `ab discuss`, conflict with the multi-UI ADR (`docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`), whether the view design matches the actual data shape served by `/api/discussions/...`.

### Section 4 — Recommendation

One paragraph: what should the orchestrator do **next** when the user is back?
- "Close as superseded by #N"
- "Push REVISE: dispatch Codex to apply revisions A, B, C"
- "Approve PROPOSED → flip to ACCEPTED on user signoff"
- "Wait for ADR-X to land first"

### Section 5 — Evidence appendix

Quoted excerpts from each file you cited, with file paths and line numbers. This is the #M-4 backing.

---

## Constraints

- **Read-only mode.** You will not write code, do not modify any source. The ONLY file you create is the REVIEW.md inside your worktree.
- **No tool other than read/grep/curl/gh.** Don't run pytest, don't run the API.
- **Don't write to `main`** — your worktree branch (`claude/1791-adr-review`) only.
- **Be the senior reviewer** — push back on weak design, don't rubber-stamp. The user's project rule #7: *"The user explicitly wants pushback. Do not rubber-stamp ideas."*

## Worktree

Dispatcher creates `.worktrees/dispatch/claude/claude-1791-adr-review/`. All work there. After you finish, your job is JUST:
1. Create `audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md`.
2. `git add audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md`
3. Commit: `docs(review): adversarial review of #1791 Decision Graph ADR`
4. Push: `git push -u origin claude/1791-adr-review`
5. Open a comment on PR #1791 with a one-paragraph summary + link to the REVIEW.md, NO PR opening (this is a review artifact, not a code PR — but pushing to the branch lets the orchestrator merge to main directly later if needed).

Actually — clarification: **don't open a PR**. The review is an audit artifact. The orchestrator merges audit/ commits directly via fast-forward. Just push to the branch.

If you'd rather open a PR for visibility, do so but title it `docs(review): adversarial review of #1791 (audit only)` and DO NOT auto-merge.

## Done criteria

- `audit/claude-review-1791-decision-graph-adr-2026-05-09/REVIEW.md` exists with all 5 sections.
- Every claim has a file/line citation.
- Pushed to `claude/1791-adr-review`.
- Comment on PR #1791 linking the review.
