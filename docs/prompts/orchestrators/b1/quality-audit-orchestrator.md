# B1 Quality Audit Orchestrator

Prompt version: 0.1
Last reviewed: 2026-06-21

## Source Assumptions

- B1 is full Ukrainian immersion in module body, with English only where current repo policy permits vocabulary glosses.
- The current B1 manifest has 94 modules. M83-M92 have built module sources in this checkout; M93-M94 may be plan/wiki-only and must not be assumed built.
- This audit is for B1 M1-M82 normalization using the M83-M94 quality bar where those files exist.
- This audit is read-only except for the durable report under `docs/audits/`.

## Goal

Run a complete B1 normalization quality audit for M1-M82, using recent B1 quality expectations from M83-M94 when present. Record every issue without top-10 truncation, including plan/wiki/research coverage, engagement boxes, stress marks, wall-of-text risks, activities, vocabulary, and M82 quality. Include a full remediation batching plan but do not fix modules.

## WORKTREE_ROOT Setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/b1-quality-audit .worktrees/dispatch/codex/b1-quality-audit origin/main
cd .worktrees/dispatch/codex/b1-quality-audit
test -e .venv || ln -s /Users/krisztiankoos/projects/learn-ukrainian/.venv .venv
export WORKTREE_ROOT="/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/b1-quality-audit"
pwd
git status --short --branch
git rev-parse --show-toplevel
```

## Read First

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `curriculum/l2-uk-en/curriculum.yaml`, B1 section
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `docs/runbooks/module-build-token-telemetry.md`
- `scripts/config.py`
- `scripts/audit/config.py`
- B1 M83-M94 inventory from `curriculum.yaml`; for each present source directory, read module, activities, vocabulary, plan, wiki, and site MDX
- Older B1 samples across M1-M82, including:
  - `curriculum/l2-uk-en/b1/b1-baseline-past-present/module.md`
  - `curriculum/l2-uk-en/b1/pluralia-tantum/module.md`
  - `curriculum/l2-uk-en/b1/complex-subordinate-condition/module.md`
  - `curriculum/l2-uk-en/b1/complex-subordinate-concess/module.md`
  - matching plans, wiki files under `wiki/grammar/b1/`, activities, vocabulary, resources, and site MDX

## Allowed Writes

- `docs/audits/b1-normalization-quality-audit-YYYY-MM-DD.md`

## Forbidden Writes

- `curriculum/l2-uk-en/**`
- `site/src/content/docs/**`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Audit Checks

- Verify B1 sequence and M1-M82 scope from `curriculum.yaml`.
- Inventory M83-M94 and explicitly record which are built, plan-only, or missing.
- Verify current B1 thresholds, immersion, grammar constraints, activity types, and stress policy from code before judging.
- Check plan coverage: objectives, content outline, dialogue situations, activity hints, vocabulary hints, and references.
- Check wiki/source coverage: `wiki/grammar/b1/<slug>.md`, `.sources.yaml`, and plan references.
- Check full Ukrainian immersion in body text; flag English body prose unless current repo policy permits it.
- Check engagement: enough callouts, dialogues, examples, and learner-relevant contexts, without decorative filler.
- Check stress marks and vocabulary stress policy from current docs/config before flagging.
- Check wall-of-text risk: long grammar prose should be broken by tables, examples, comparison boxes, and activities.
- Check activities and vocabulary against the target module focus and current `scripts/audit/config.py`.
- Check M82 specifically as the final pre-M83 normalization boundary; note any quality discontinuity before `reported-speech`.
- Record all findings and group them into targeted patch batches, full rebuild candidates, source/wiki gaps, and validation/tooling issues.

## Helpers And Headroom

Read-only helpers are allowed for module inventories or coverage matrices. Do not delegate final severity calls. Use Headroom compression for helper output or searches over 200 lines or 20 KB.

## Durable Report Path

Write the report to `docs/audits/b1-normalization-quality-audit-YYYY-MM-DD.md`.

## Validation Commands

```bash
git status --short --branch
git diff --check
git diff --name-only
git diff --name-only | rg -v '^docs/audits/b1-normalization-quality-audit-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' || true
rg -n 'sys\.executable' docs/audits/b1-normalization-quality-audit-*.md
```

Do not run builds. Do not write generated curriculum audit/status/review artifacts.

## Expected Final Response

```text
Report written: docs/audits/b1-normalization-quality-audit-YYYY-MM-DD.md
Scope inspected: M1-M82 plus M83-M94 bar inventory
Blockers: <n>
Issues recorded: <n>
Recommended remediation batches: <summary>
Validation run: <commands and outcomes>
Curriculum files modified: no
swarm_used: true/false
swarm_note: <helpers used, or solo run; no swarm used>
```
