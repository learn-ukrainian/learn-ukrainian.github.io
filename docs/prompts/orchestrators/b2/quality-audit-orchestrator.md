# B2 Quality Audit Orchestrator

Prompt version: 0.1
Last reviewed: 2026-06-21

## Source Assumptions

- This is a post-build audit for B2 modules, not a preflight plan audit.
- B2 should show higher abstraction, richer syntax, stylistic/register control, argumentation, and professional/academic readiness.
- The audit is read-only except for the durable report under `docs/audits/`.
- Do not assume every planned B2 module is built; audit only built modules in scope and record missing source directories separately.

## Goal

Review built B2 modules for B2-specific quality after production. Record a complete issue inventory without top-10 truncation, write a durable report, and propose remediation batches. Do not fix modules.

## WORKTREE_ROOT Setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/b2-quality-audit .worktrees/dispatch/codex/b2-quality-audit origin/main
cd .worktrees/dispatch/codex/b2-quality-audit
test -e .venv || ln -s /Users/krisztiankoos/projects/learn-ukrainian/.venv .venv
export WORKTREE_ROOT="/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/b2-quality-audit"
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
- target B2 production PR notes or build report if available
- for each built target slug:
  - `curriculum/l2-uk-en/plans/b2/<slug>.yaml`
  - `curriculum/l2-uk-en/b2/discovery/<slug>.yaml`
  - `curriculum/l2-uk-en/b2/<slug>/module.md`
  - `curriculum/l2-uk-en/b2/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/b2/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/b2/<slug>/resources.yaml` if present
  - `wiki/grammar/b2/<slug>.md`
  - `wiki/grammar/b2/<slug>.sources.yaml`
  - `site/src/content/docs/b2/<slug>.mdx`

## Allowed Writes

- `docs/audits/b2-quality-audit-YYYY-MM-DD.md`

## Forbidden Writes

- `curriculum/l2-uk-en/**`
- `wiki/**`
- `site/src/content/docs/**`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Audit Checks

- Verify built-module scope against `curriculum.yaml`; record planned but unbuilt modules separately.
- Verify live B2 thresholds, immersion policy, activity types, and grammar constraints from code.
- Check plan fidelity: objectives, content outline, vocabulary hints, activity hints, phase goals, and references.
- Check source/wiki coverage and whether the module teaches from the local wiki rather than inventing source claims.
- Check B2 abstraction: advanced concepts are explained in Ukrainian without becoming opaque.
- Check richer syntax: multi-clause sentences are natural, controlled, and teachable; complexity is not decorative.
- Check register and style: formal/informal, business, academic, public discourse, literary, and cross-register tasks match the module goal.
- Check argumentation and professional/academic readiness: learners practice claims, evidence, counterargument, synthesis, reports, presentations, or analysis where appropriate.
- Check activities: they practice language skills, not trivia about the topic.
- Check vocabulary: enough B2 terms, register labels where useful, natural examples, and source-backed usage.
- Check engagement and wall-of-text risk: examples, tables, callouts, and tasks make dense material usable.

## Helpers And Headroom

Read-only helpers are allowed for coverage matrices or validation summaries. Do not delegate final severity calls. Use Headroom compression for helper output or logs over 200 lines or 20 KB.

## Durable Report Path

Write the report to `docs/audits/b2-quality-audit-YYYY-MM-DD.md`.

## Validation Commands

```bash
git status --short --branch
git diff --check
git diff --name-only
git diff --name-only | rg -v '^docs/audits/b2-quality-audit-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' || true
rg -n 'sys\.executable' docs/audits/b2-quality-audit-*.md
```

Do not run builds. Do not write generated curriculum audit/status/review artifacts.

## Expected Final Response

```text
Report written: docs/audits/b2-quality-audit-YYYY-MM-DD.md
Scope inspected: <modules>
Blockers: <n>
Issues recorded: <n>
Recommended remediation batches: <summary>
Validation run: <commands and outcomes>
Curriculum files modified: no
swarm_used: true/false
swarm_note: <helpers used, or solo run; no swarm used>
```
