# LIT-DRAMA Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- `lit-drama` is an active LIT specialization track for drama, performance, dialogue, staging, and theatre history.
- Treat plays, scenes, stage directions, performance manifestos, reviews, and theatre documents as reading candidates when rights allow.
- Record unavailable or copyrighted drama texts as linked-only, excerpt-only, or `reading-needed`; do not paste full copyrighted plays.

## Goal

Run preflight, production, quality audit, or remediation for scoped `lit-drama` modules without touching B2 or inactive LIT remnants.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-drama-<stage>-<batch> .worktrees/dispatch/codex/lit-drama-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-drama-<stage>-<batch>
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
- `docs/l2-uk-en/templates/lit-module-template.md`
- `docs/status/LIT-DRAMA-STATUS.md`
- target `curriculum/l2-uk-en/plans/lit-drama/<slug>.yaml`
- existing target source, sidecars, readings, and `site/src/content/docs/lit-drama/<slug>.mdx` when present

## Allowed Writes

- `docs/audits/lit-drama-<scope>-<date>.md`
- scoped current-layout files under `curriculum/l2-uk-en/lit-drama/`
- `site/src/content/docs/lit-drama/<slug>.mdx`
- hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- inactive `lit-crimea` or `lit-doc` prompt/source work
- non-hostable copyrighted full scripts or performance recordings
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: verify active plans, drama text availability, performance/source context, and reading rights.
- Production: center close reading of dialogue, staging, conflict, performance context, and theatre history.
- Quality audit: check quote fidelity, scene attribution, rights, Ukrainian theatre framing, and activity quality.
- Remediation: fix reading/copyright/source blockers before prose polish.

## Track-Specific Checks

- Distinguish literary text from performance adaptation; cite the edition or production being discussed.
- Do not treat video recordings, theatre photos, or posters as hostable without separate rights verification.

## Helpers And Headroom

Use helpers for text/source discovery and rights classification. Compress long results with Headroom.

## Validation Commands

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/lit-drama").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit-drama plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Add current module, sidecar, MDX, and site checks when production/remediation writes content.

## Expected Final Response

```text
LIT-DRAMA stage: <preflight | production | quality-audit | remediation>
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
