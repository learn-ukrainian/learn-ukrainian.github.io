# C1 Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- C1 is an advanced core track for academic, professional, stylistic, cultural, and linguistic mastery; it is not BIO and must not absorb BIO-specific biography work.
- The current C1 source base includes `curriculum/l2-uk-en/plans/c1/*.yaml`, `curriculum/l2-uk-en/c1/discovery/*.yaml`, `docs/l2-uk-en/C1-PLAN-GENERATED.md`, and `docs/l2-uk-en/templates/c1-module-template.md`.
- Plans and current config are source of truth. If old templates and plans disagree on word targets or structure, record a preflight finding before production.
- This suite covers preflight, production, quality audit, and remediation. Use only the stage that matches the task.

## Goal

Run C1 work in scoped batches without touching B2 or seminar tracks. Verify plan/discovery readiness, build or remediate modules with university-level Ukrainian, audit for C1 quality, and keep generated artifacts out of the PR.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/c1-<stage>-<batch> .worktrees/dispatch/codex/c1-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/c1-<stage>-<batch>
test -e .venv || ln -s "$REPO_ROOT/.venv" .venv
export WORKTREE_ROOT="$(pwd)"
pwd
git status --short --branch
git rev-parse --show-toplevel
```

## Read First

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/l2-uk-en/C1-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/c1-module-template.md`
- `docs/l2-uk-en/templates/c1-academic-module-template.md`
- `docs/l2-uk-en/templates/c1-checkpoint-module-template.md`
- `docs/plans/c1-state-standard-gap-analysis.md`
- target `curriculum/l2-uk-en/plans/c1/<slug>.yaml`
- target `curriculum/l2-uk-en/c1/discovery/<slug>.yaml` when present
- existing target source and `site/src/content/docs/c1/<slug>.mdx` when present

## Allowed Writes

- Preflight or quality audit: `docs/audits/c1-<scope>-<date>.md`
- For scoped C1 target slugs only:
  - `curriculum/l2-uk-en/c1/<slug>/module.md`
  - `curriculum/l2-uk-en/c1/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/c1/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/c1/<slug>/resources.yaml`
  - `site/src/content/docs/c1/<slug>.mdx`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- plans, discovery, or wiki files unless the stage explicitly scopes a readiness remediation
- modules outside the selected C1 batch
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: compare plans, discovery files, generated plan docs, current config thresholds, and available source/wiki coverage. Block production on unresolved plan/discovery contradictions.
- Production: build one module at a time with C1 academic depth, 100% Ukrainian immersion except permitted vocabulary glosses, precise register control, and serious writing support.
- Quality audit: verify C1 content against academic/professional/stylistic expectations, not B1/B2 simplification.
- Remediation: fix every selected audit finding in PR-sized batches and regenerate MDX through current tooling.

## Track-Specific Checks

- Preserve the C1 shift from language practice to studying in Ukrainian: comparative analysis, academic argument, source handling, register mastery, and complex syntax.
- Do not backfill content with generic cultural trivia; each module needs a defensible advanced-language purpose.
- Check that C1 cultural modules do not duplicate FOLK seminar reading rules unless the plan explicitly asks for primary-source seminar work.

## Helpers

Use one to three helpers only for plan/discovery inventory, targeted validation, or source lookup. Summarize long outputs; push bulky evidence behind a file path or PR link. The main orchestrator owns scope, edits, review routing, and merge readiness.

## Validation Commands

Adapt module numbers from `curriculum/l2-uk-en/curriculum.yaml`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en c1 <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/c1/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en c1 <module_num> --validate
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1/<slug>/module.md
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Run the forbidden-artifact guard from `shared/validation-checklist.md` before staging.

## Expected Final Response

```text
C1 stage: <preflight | production | quality-audit | remediation>
Scope: <slugs or audit report>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted | not module-build | unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
