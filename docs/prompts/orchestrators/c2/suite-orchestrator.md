# C2 Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- C2 is the final core track: native-level style, literary mastery, professional specialization, teaching, translation, and capstone work.
- Current sources include `curriculum/l2-uk-en/plans/c2/*.yaml`, `curriculum/l2-uk-en/c2/discovery/*.yaml`, `docs/l2-uk-en/C2-PLAN-GENERATED.md`, and `docs/l2-uk-en/templates/c2-module-template.md`.
- Older C2 templates and generated plan docs can disagree on word targets. Treat plans/config as source of truth and record mismatches in preflight before production.
- C2 may use authentic literary or professional texts, but it is still a core CEFR track; do not import seminar reading-floor requirements unless a plan explicitly needs source-text work.

## Goal

Run C2 preflight, production, quality audit, or remediation without touching B2. Build native-level Ukrainian modules with verified authentic sources, no invented quotes, and full validation.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/c2-<stage>-<batch> .worktrees/dispatch/codex/c2-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/c2-<stage>-<batch>
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
- `docs/l2-uk-en/C2-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/c2-module-template.md`
- `docs/l2-uk-en/templates/c2-literary-module-template.md`
- `docs/l2-uk-en/templates/c2-professional-module-template.md`
- `docs/l2-uk-en/templates/c2-style-module-template.md`
- target `curriculum/l2-uk-en/plans/c2/<slug>.yaml`
- target `curriculum/l2-uk-en/c2/discovery/<slug>.yaml` when present
- existing target source and `site/src/content/docs/c2/<slug>.mdx` when present

## Allowed Writes

- Preflight or quality audit: `docs/audits/c2-<scope>-<date>.md`
- For scoped C2 target slugs only:
  - `curriculum/l2-uk-en/c2/<slug>/module.md`
  - `curriculum/l2-uk-en/c2/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/c2/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/c2/<slug>/resources.yaml`
  - `site/src/content/docs/c2/<slug>.mdx`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- unrelated C2 modules or lower-level core tracks
- plans or discovery files unless the task explicitly scopes readiness remediation
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: resolve plan/config/template mismatches, source availability, and whether target modules need authentic text or professional-domain evidence before writing.
- Production: write one module at a time. C2 work must show expert register, stylistic transformation, professional precision, or creative control; no simplified filler.
- Quality audit: check native-level quality, authentic-source fidelity, task/model-answer completeness, and whether production tasks actually test C2 control.
- Remediation: fix selected findings, regenerate MDX, and rerun validation without broad refactors.

## Track-Specific Checks

- Never invent literary quotes, professional terminology, legal/medical forms, or stylistic analyses. Verify against authentic Ukrainian sources when the plan depends on them.
- Preserve the C2 shift from understanding Ukrainian to creating, transforming, teaching, translating, and polishing with Ukrainian.
- Keep learner tasks production-focused: transformations, critiques, portfolios, oral defense, professional documents, translation, and capstone artifacts.

## Helpers

Use helpers for source verification, domain terminology checks, and validation only when they materially reduce risk. Summarize long helper output; push bulky evidence behind a file path or PR link.

## Validation Commands

Adapt module numbers from `curriculum/l2-uk-en/curriculum.yaml`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en c2 <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/c2/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en c2 <module_num> --validate
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c2/<slug>/module.md
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Run the forbidden-artifact guard from `shared/validation-checklist.md` before staging.

## Expected Final Response

```text
C2 stage: <preflight | production | quality-audit | remediation>
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
