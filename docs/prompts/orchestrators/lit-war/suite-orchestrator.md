# LIT-WAR Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- `lit-war` is an active contemporary war literature track. It is time-sensitive and requires trauma-aware, source-grounded handling.
- Current planning docs include `docs/l2-uk-en/LIT-WAR-PLAN-GENERATED.md` and active plans under `curriculum/l2-uk-en/plans/lit-war/`.
- Most texts are recent and copyrighted. Default to linked-only or excerpt-only unless explicit hostable rights are verified.

## Goal

Run preflight, production, audit, or remediation for scoped `lit-war` modules, preserving Ukrainian agency, testimony, rights, and learner-safe framing.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-war-<stage>-<batch> .worktrees/dispatch/codex/lit-war-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-war-<stage>-<batch>
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
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- `docs/l2-uk-en/LIT-WAR-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/lit-module-template.md`
- target `curriculum/l2-uk-en/plans/lit-war/<slug>.yaml`

## Allowed Writes

- `docs/audits/lit-war-<scope>-<date>.md`
- scoped files under `curriculum/l2-uk-en/lit-war/`
- `site/src/content/docs/lit-war/<slug>.mdx`
- hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- inactive LIT remnants
- non-hostable full contemporary texts, captivity images, or propaganda-origin media
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: verify text identity, author context, rights, sensitivity risks, and current-event claims.
- Production: frame as literature of resistance and testimony, not neutral "conflict literature" or tragedy-on-both-sides prose.
- Quality audit: check trauma-aware framing, agency, rights, source dates, and no Russian propaganda laundering.
- Remediation: fix safety, source, reading, and copyright blockers before style polish.

## Track-Specific Checks

- Treat fallen authors and captivity testimony with dignity, not sentimentality.
- Use absolute dates for recent events and verify them against current reliable sources.

## Helpers And Headroom

Use helpers for current-source verification, rights checks, and trauma/safety review. Compress long outputs with Headroom.

## Validation Commands

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/lit-war").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit-war plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Add content-generation validation for production/remediation.

## Expected Final Response

```text
LIT-WAR stage: <preflight | production | quality-audit | remediation>
Scope: <slugs or audit report>
Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted | not module-build | unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
