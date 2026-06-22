# ISTORIO Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- ISTORIO is an advanced historiography seminar track after HIST, not a
  replacement for HIST modules or C1 core work.
- Current sources include `curriculum/l2-uk-en/plans/istorio/*.yaml`,
  `curriculum/l2-uk-en/istorio/`,
  `site/src/content/docs/istorio/`, `docs/l2-uk-en/C1-HIST-PLAN-GENERATED.md`,
  and history textbook/source references under `docs/references/`.
- Every module needs a reading catalog with primary documents, historiographic
  excerpts, or source-methodology readings. If a text is unavailable or rights
  are unclear, record `reading-needed`; do not omit the reading layer.
- This suite covers preflight, production, quality audit, and remediation. Use
  only the stage that matches the task.

## Goal

Orchestrate ISTORIO batches without touching B2. Build historiography modules
around primary sources, competing interpretations, decolonized methodology, and
explicit source criticism.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/istorio-<stage>-<batch> .worktrees/dispatch/codex/istorio-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/istorio-<stage>-<batch>
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
- relevant history references under `docs/references/`
- target `curriculum/l2-uk-en/plans/istorio/<slug>.yaml`
- existing target source, sidecars, readings, and
  `site/src/content/docs/istorio/<slug>.mdx` when present

## Allowed Writes

- Preflight or quality audit: `docs/audits/istorio-<scope>-<date>.md`
- For scoped ISTORIO target slugs only:
  - current-layout source files under `curriculum/l2-uk-en/istorio/`
  - sidecars under `curriculum/l2-uk-en/istorio/{meta,activities,vocabulary}/`
    when the current layout uses them
  - `site/src/content/docs/istorio/<slug>.mdx`
  - hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- HIST, C1, or C2 modules unless the task explicitly scopes cross-track
  remediation
- plans, textbook references, wiki/source registries, or unrelated tracks unless
  explicitly scoped
- non-hostable copyrighted full texts under `site/src/content/readings/`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and
  `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: inventory primary documents, historiographic schools, source
  availability, copyright status, and any plan/source contradictions before
  production.
- Production: begin from source work and historiographic method, then build
  lecture prose, readings, vocabulary, and seminar tasks around a defensible
  argument.
- Quality audit: verify factual claims, source provenance, historiographic
  attribution, decolonization framing, and reading-link behavior.
- Remediation: fix ghost sources, factuality, and framing blockers before
  language polish.

## Track-Specific Checks

- Distinguish primary evidence, historiographic interpretation, and memory
  politics in every module.
- Do not treat Russian imperial or Soviet historiography as neutral authority.
- When a topic is contested, name the competing interpretations and the source
  basis for each one.
- Regional, Crimean Tatar, Jewish, Polish, diaspora, and other perspectives must
  be source-grounded, not token additions.

## Helpers And Headroom

Use helpers for source inventory, rights classification, and historiographic
cross-checks. Compress long source surveys with Headroom before passing them
between agents.

## Validation Commands

Adapt to current target layout:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/istorio").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("istorio plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

For built modules, add the current sidecar, MDX, reading, and site validation
commands from `shared/validation-checklist.md`.

## Expected Final Response

```text
ISTORIO stage: <preflight | production | quality-audit | remediation>
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
