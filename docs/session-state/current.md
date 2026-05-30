# Current - Codex thread handoff (2026-05-30T19:20:00Z)

Latest-Brief: docs/session-state/current.md

> Handoff-only update by the Codex orchestrator. Treat `origin/main` and this
> file as authoritative.

## Thread Lease

- Active generation: `orchestrator-next-20260530T092511Z`
- Replacement thread id: `019e7836-06ef-7973-a630-07824922dfe5`
- Replacement status: `started`
- Old automation ready to delete was previously confirmed true, but do not
  delete or pause old automation unless the user explicitly instructs it.

## Exact Continuation

The user redirected Codex back to the brainstorm operating model:

- BIO is Claude-owned. Do not keep driving BIO from this Codex thread except for
  requested review/sign-off or repo-wide tooling.
- Codex owns A1 golden path, issue memory, orchestration, and pipeline hygiene.
- Before more broad production, run the first GitHub issue triage cycle.

That triage cycle is complete:

- 71 open issues audited.
- New labels created:
  - `lane:a1`, `lane:bio`, `lane:infra`, `lane:docs`, `lane:corpus`,
    `lane:orchestration`, `lane:archive`
  - `state:now`, `state:next`, `state:blocked`,
    `state:archive-candidate`, `state:owned-by-claude`
- Every open issue now has at least one `lane:*` label and one `state:*` label.
- BIO issues are labeled `lane:bio`, `agent:claude`, and
  `state:owned-by-claude`.
- A1 golden-path issues are labeled `lane:a1` and `agent:codex`.
- No issues were closed.
- Proposed archive/duplicate closures were only labeled and must be reviewed
  before any closure.
- Open PRs were also labeled into the board:
  - #2447 `lane:a1`, `state:now`, `agent:codex`
  - #2450 `lane:orchestration`, `state:now`, `agent:codex`

## Active Board

### A1 Golden Path - Codex

- #2447 PR: `fix(build): normalize stressed plan section headings` (draft,
  clean at triage time)
- #2389: rebuild `a1/my-morning` under clean wiki-driven pipeline and ship the
  anchor
- #2390: pilot m21 + m22 after m20 ships
- #2418: add correction path for retrieval-discipline gate omissions
- #2419: deterministic heritage-defense gate for authentic Ukrainian forms
- #2380: V7.1 build pipeline regressions surfaced by m20 pilot

### Orchestration / Infra - Codex

- #2450 PR: agent-specific thread routers (open, dirty against main at triage)
- #2448: support agent-specific thread handoff files
- #2368: `/api/delegate/active` route mismatch versus `/api/orient`
- #2126: `review/review` GitHub action instability

### BIO - Claude

- #2309: BIO expansion epic
- #2451: four merged BIO dossiers below 1200-word floor
- BIO child issues remain labeled for Claude ownership; Codex should not start
  them unless the user explicitly redirects.

## Proposed Archive / Duplicate Review

Do not close these without explicit review:

- #2351 likely superseded by broader #2418 retrieval-discipline correction path.
- #1969 likely superseded by broader #2418 retrieval-discipline correction path.
- #2132 looks like a stale promote-protocol result thread; verify whether any
  action remains before closing.

## Current Git State

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Branch: `main`
- Latest HEAD before this handoff commit: `90235bc878`
- Upstream: `origin/main`
- Active delegates: 0 at last check.
- Open PRs at triage:
  - #2450 `feat(handoff): add agent-specific thread routers`
  - #2447 draft `fix(build): normalize stressed plan section headings`

## Next Decisive Action

Start from the active board, not from BIO:

1. Inspect #2447 and either finish the independent review/undraft/merge path or
   record the blocker.
2. If #2447 merges, continue #2389 and rebuild/evaluate the A1 m20 anchor.
3. Keep #2418/#2419 as the next A1 gate fixes if m20 exposes those blockers.
4. Leave BIO Phase 2 production to Claude.

## Validation Already Run

- `gh issue list --state open --limit 200 --json number,title,labels,url`
- Audit confirmed:
  - open issues: 71
  - missing `lane:*`: 0
  - missing `state:*`: 0
- `gh issue list --label state:now` used to produce the active board.
- `gh issue list --label state:archive-candidate` used to produce the proposed
  archive/duplicate review list.

## Guardrails

- Keep the main checkout read-only except handoff updates.
- Use `.worktrees/dispatch/<agent>/<task>/` for implementation.
- Do not edit generated status/audit/review artifacts, linter configs, or
  `.python-version`.
- Every commit must carry an `X-Agent` trailer.
- Do not delete or pause old heartbeat automation unless the user explicitly
  instructs it.
