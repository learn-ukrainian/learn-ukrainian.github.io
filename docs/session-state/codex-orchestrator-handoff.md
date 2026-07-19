# Current - Codex / Grok Orchestrator Handoff (2026-07-19)

Latest-Brief: docs/session-state/2026-07-19-orchestrator-practice-atlas-fleet-comms-finish-brief.md

## Role

Orchestrator seat (Codex / Grok / Claude-infra as assigned): drive the product and
infra queue, keep main clean, open PRs from worktrees only, require cross-family
`review-pr` before merge, arm auto-merge after the gate, clean worktrees after merge.
Do not babysit idle green PRs; do not leave draft limbo.

Do not use `docs/session-state/current.md` as scratch space. Durable state lives in
the Latest-Brief above and this file. Thread rollover packets live under
`.agent/<agent>-thread-handoff.md` (machine-local).

## Current State (session close 2026-07-19)

Finish wave **closed**. Main at ~`b845eb95b5` (and successors once this handoff PR merges).

### Shipped / closed

- Practice chrome dual-locale residuals: **#5479** (#5355)
- Paronym expansion + apostrophe fix: **#5480**, **#5489** (#4506)
- Source-backed sentence inventory for daily: **#5487** (#5483 closed)
- Textbook bulk promote with enrichment floor: **#5477** (#3934); backlog **#5478** open
- Fleet doctrine + Haiku recon: **#5474**, **#5475**
- Fleet-comms Sol phases 0–5 epic **#5484** closed via **#5488** (#5485/#5486)
- Warn-not-reject fat formal PR CF ask (prefer `review-pr`): **#5491**

### Explicit non-goals for next cold-start

- Do not re-litigate closed fleet-comms phases 0–5
- Do not re-promote unenriched textbook heads without #5478 enrichment work
- Do not import Clozemaster as a product; inventory is multi-surface / corpus-first

## Operating Rules

- Implementation only under `.worktrees/dispatch/<agent>/<task>/`
- Every commit: `X-Agent` trailer
- Use `.venv/bin/python`, never `sys.executable`
- Never touch `.python-version`, `.yamllint`, `.markdownlint.json`
- No status/audit/review artifact dumps in code PRs
- CF review gate = independent cross-family `review-pr` (discuss ≠ review)
- Prefer activity/practice product work over textbook re-enrich unless reprioritized

## Startup Checks

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main --prune
git status --short --branch
gh pr list --state open --json number,title,isDraft,mergeStateStatus,headRefName,url --limit 30
curl -sS --max-time 2 "http://127.0.0.1:8765/api/orient?lean=true" || true
# Read latest brief:
# docs/session-state/2026-07-19-orchestrator-practice-atlas-fleet-comms-finish-brief.md
```

## Next Focus

1. Spot-check live daily practice examples (inventory #5487 already merged).
2. When enrichment capacity is intentional: **#5478** re-enrich held textbook heads.
3. Atlas/practice depth: #4387, #4700, #4707, #5411 (glosses via enrich, not raw inject).
4. Infra backlog only when free: #5392, #5400, #5366, #5472 (prep prove-out).
