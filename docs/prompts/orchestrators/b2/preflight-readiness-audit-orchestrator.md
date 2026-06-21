# B2 Preflight Readiness Audit Orchestrator

Prompt version: 0.1
Last reviewed: 2026-06-21

## Source Assumptions

- B2 is the upcoming production track. Do not build modules until readiness passes.
- Current local repo contains B2 plans, discovery YAML, and wiki grammar/source files; built `curriculum/l2-uk-en/b2/<slug>/module.md` directories may not exist.
- Check Ukrainian State Standard 2024 alignment only through repo-supported sources, plan references, source YAML, and local docs. Do not invent external standards or unsupported claims.
- This audit is read-only except for the durable report under `docs/audits/`.

## Goal

Determine whether B2 is ready for module production. Validate plans, sequence, `curriculum.yaml` alignment, wiki/grammar articles, source YAML coverage, research/source coverage, stale slugs, sequencing, and standard-alignment blockers. Output a readiness report with explicit "do not build until fixed" blockers. Do not fix plans or build modules.

## WORKTREE_ROOT Setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/b2-preflight-readiness .worktrees/dispatch/codex/b2-preflight-readiness origin/main
cd .worktrees/dispatch/codex/b2-preflight-readiness
test -e .venv || ln -s /Users/krisztiankoos/projects/learn-ukrainian/.venv .venv
export WORKTREE_ROOT="/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/b2-preflight-readiness"
pwd
git status --short --branch
git rev-parse --show-toplevel
```

## Read First

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `curriculum/l2-uk-en/curriculum.yaml`, B2 section
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`
- `scripts/audit/config.py`
- all B2 plans under `curriculum/l2-uk-en/plans/b2/`
- all B2 discovery files under `curriculum/l2-uk-en/b2/discovery/`
- all B2 wiki and source files under `wiki/grammar/b2/`
- relevant local docs or plan references that mention Ukrainian State Standard 2024

## Allowed Writes

- `docs/audits/b2-preflight-readiness-YYYY-MM-DD.md`

## Forbidden Writes

- `curriculum/l2-uk-en/**`
- `wiki/**`
- `site/src/content/docs/**`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Readiness Checks

- Confirm every B2 slug in `curriculum.yaml` has exactly one plan file.
- Confirm every plan slug and sequence matches the manifest.
- Confirm discovery YAML coverage for every planned B2 slug.
- Confirm `wiki/grammar/b2/<slug>.md` and `<slug>.sources.yaml` coverage for every planned B2 slug.
- Identify stale plan files, `.bak` files, orphan wiki files, missing discovery files, missing source YAML, and naming mismatches.
- Check plan quality: objectives, content outline, vocabulary hints, activity hints, references, phase labels, and B2-appropriate register.
- Check sequencing: prerequisites appear before dependent modules; checkpoints and domain vocabulary are positioned coherently.
- Check source coverage against repo-supported Ukrainian State Standard 2024 references. If support is absent, record a source gap instead of inventing alignment.
- Identify blockers that require plan/wiki/source work before production.
- Mark readiness as `pass`, `conditional pass`, or `do not build`.

## Helpers And Headroom

Read-only helpers are allowed for inventories or slug-matrix checks. The main auditor owns readiness judgment. Use Headroom compression for helper output or search results over 200 lines or 20 KB.

## Durable Report Path

Write the report to `docs/audits/b2-preflight-readiness-YYYY-MM-DD.md`.

## Validation Commands

```bash
.venv/bin/python scripts/validate_plans.py b2
git status --short --branch
git diff --check
git diff --name-only
git diff --name-only | rg -v '^docs/audits/b2-preflight-readiness-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' || true
rg -n 'sys\.executable' docs/audits/b2-preflight-readiness-*.md
```

Do not run builds. Do not modify B2 plans, wiki files, discovery files, or modules.

## Expected Final Response

```text
Report written: docs/audits/b2-preflight-readiness-YYYY-MM-DD.md
Readiness status: pass | conditional pass | do not build
Blockers: <n>
Source/wiki/plan gaps: <summary>
Validation run: <commands and outcomes>
B2 production allowed now: yes/no
Curriculum files modified: no
swarm_used: true/false
swarm_note: <helpers used, or solo run; no swarm used>
```
