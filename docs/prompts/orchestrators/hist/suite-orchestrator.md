# HIST Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- HIST is a seminar history track. It needs primary historical readings, source criticism, decolonized framing, and careful treatment of contested memory.
- Current source surfaces include `curriculum/l2-uk-en/plans/hist/*.yaml`, `curriculum/l2-uk-en/hist/`, `docs/l2-uk-en/C1-HIST-PLAN-GENERATED.md`, `docs/l2-uk-en/C1-HIST-10-10-IMPROVEMENT-PLAN.md`, and history textbook references under `docs/references/textbooks-txt/`.
- Every module must identify a researched catalog of primary/source readings. If a text is unavailable or rights are unclear, record `reading-needed`; do not omit the reading layer.
- This suite covers preflight, production, quality audit, and remediation. Use only the stage that matches the task.

## Goal

Orchestrate HIST batches without touching B2. Verify source/readings readiness, build history seminar modules, audit factuality and framing, and remediate findings in small PRs.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/hist-<stage>-<batch> .worktrees/dispatch/codex/hist-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/hist-<stage>-<batch>
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
- `docs/l2-uk-en/C1-HIST-PLAN-GENERATED.md`
- `docs/l2-uk-en/C1-HIST-10-10-IMPROVEMENT-PLAN.md`
- relevant `docs/references/textbooks-txt/*history*.txt`
- target `curriculum/l2-uk-en/plans/hist/<slug>.yaml`
- existing target source, resources, readings, and `site/src/content/docs/hist/<slug>.mdx` when present

## Allowed Writes

- Preflight or quality audit: `docs/audits/hist-<scope>-<date>.md`
- For scoped HIST target slugs only:
  - current-layout source files under `curriculum/l2-uk-en/hist/`
  - `site/src/content/docs/hist/<slug>.mdx`
  - hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- plans, textbook references, wiki/source registries, or unrelated tracks unless explicitly scoped
- non-hostable copyrighted full texts under `site/src/content/readings/`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: enumerate primary documents per target module, classify hosting rights, and block on ghost sources or missing source packs.
- Production: build around source work first: document excerpt, provenance, context, competing interpretations, then seminar tasks.
- Quality audit: verify date/person/place claims, source provenance, Russian-imperial/Soviet framing, and reading-link behavior.
- Remediation: fix factuality, reading, and framing findings before style polish.

## Track-Specific Checks

- Historical claims need explicit support from textbook, primary, scholarly, or source-registry evidence.
- Avoid "both sides" flattening for Russian imperial, Soviet, and Russian Federation violence.
- Name contested memory and historiography honestly, including Polish, Jewish, Crimean Tatar, regional, and diaspora perspectives when relevant.

## Helpers And Headroom

Use read-only helpers for primary-document discovery, source verification, and decolonization review. Compress long outputs with Headroom.

## Validation Commands

Adapt to current target layout:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/hist").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("hist plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

For built modules, add the relevant activity, vocabulary, MDX generation, audit, and site checks from `shared/validation-checklist.md`.

## Expected Final Response

```text
HIST stage: <preflight | production | quality-audit | remediation>
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
