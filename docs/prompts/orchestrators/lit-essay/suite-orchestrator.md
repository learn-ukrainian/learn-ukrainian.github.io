# LIT-ESSAY Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- `lit-essay` is an active intellectual essay and Ukrainian thought track: essays, pamphlets, polemics, criticism, decolonization arguments, and war-era public thought.
- Current planning docs include `docs/l2-uk-en/LIT-ESSAY-PLAN-GENERATED.md` and active plans under `curriculum/l2-uk-en/plans/lit-essay/`.
- Every module needs primary argument readings: the essay/pamphlet/publicistic text under study, or a rights-safe excerpt/link.

## Goal

Run preflight, production, quality audit, or remediation for scoped `lit-essay` modules with argument-centered seminar pedagogy and explicit reading/copyright decisions.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-essay-<stage>-<batch> .worktrees/dispatch/codex/lit-essay-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-essay-<stage>-<batch>
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
- `docs/l2-uk-en/LIT-ESSAY-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/lit-module-template.md`
- target `curriculum/l2-uk-en/plans/lit-essay/<slug>.yaml`

## Allowed Writes

- `docs/audits/lit-essay-<scope>-<date>.md`
- scoped current-layout files under `curriculum/l2-uk-en/lit-essay/`
- `site/src/content/docs/lit-essay/<slug>.mdx`
- hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- inactive `lit-crimea` or `lit-doc` work
- non-hostable copyrighted essays or excerpts beyond compliant limits
- protected configs, generated status/audit/review artifacts, and `data/telemetry/**`

## Lifecycle Rules

- Preflight: verify the essay text, edition, date, rights, intellectual context, and counterargument sources.
- Production: teach the argument's structure, assumptions, rhetoric, historical stakes, and contemporary relevance.
- Quality audit: reject vague "idea history" summaries; require source-grounded claims and argument analysis.
- Remediation: repair reading/citation/copyright blockers before style polish.

## Track-Specific Checks

- Analyze all ideologies critically, including Ukrainian nationalism; decolonization does not mean hagiography.
- Keep secondary scholarship separate from the primary essay text unless the scholar's essay is itself the object of study.

## Helpers And Headroom

Use helpers for text location, rights, and argument-map verification. Compress long outputs with Headroom.

## Validation Commands

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/lit-essay").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit-essay plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Add module, sidecar, MDX, and site checks for content-writing stages.

## Expected Final Response

```text
LIT-ESSAY stage: <preflight | production | quality-audit | remediation>
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
