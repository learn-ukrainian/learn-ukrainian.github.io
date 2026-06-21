# Shared Review Output Schema

Prompt suite component version: 0.2
Last reviewed: 2026-06-21

Use this schema for durable audit reports under `docs/audits/`. Adapt the track fields and coverage matrices to the target. Do not import CEFR language-learning assumptions into seminar tracks unless the target prompt explicitly justifies them.

## Report Header

```markdown
# <LEVEL> <SCOPE> Quality Audit

Report version: 0.1
Date: YYYY-MM-DD
Auditor: <agent/model>
Worktree: <absolute worktree path>
Scope: <levels/modules inspected>
Read-only: true
Durable report path: docs/audits/<file>.md
Source files inspected:
- <path>

Repo assumptions verified:
- <fact and source path>
```

## Executive Summary

Include:

- pass/fail or readiness status
- blocker count
- non-blocking issue count
- modules with no findings
- modules not inspected and why
- whether any local command was unavailable

## Complete Issue Inventory

Do not truncate to a top 10. Record every issue found.

```markdown
## Issues

### <ISSUE-ID> <short title>

Severity: blocker | high | medium | low
Track or level: <A1 | A2 | B1 | B2 | HIST | BIO | ISTORIO | LIT | OES | RUTH | other>
Module: <M## slug>
Files:
- <path>
Evidence:
- <short quote or paraphrase with section>
Why it matters:
- <learner, linguistic, source, or pipeline risk>
Expected fix:
- <specific remediation>
Batch recommendation:
- <batch id or "single-module patch">
```

## Coverage Matrices

Use compact tables for:

- plan objectives covered
- wiki/source coverage
- activity coverage and type variety
- vocabulary completeness
- immersion and language-balance observations
- stress/pronunciation policy observations
- factuality, source-attribution, decolonization, and bias checks for seminar or sensitive tracks
- module-specific blocker summary

## Remediation Batching Plan

Group findings into PR-sized batches. Separate:

- targeted patches
- full module rebuilds
- source/wiki gaps that need pre-build work
- generator or validation issues
- deferred decisions that need user input

## Final Auditor Response Schema

```text
Report written: <path>
Scope inspected: <modules>
Blockers: <n>
Issues recorded: <n>
Recommended next batch: <batch id>
Validation run: <commands>
Files changed: <only docs/audits report, or none>
swarm_used: true/false
swarm_label: <none | solo | helper | swarm>
swarm_note: <what helpers did, or solo run; no swarm used>
```
