# LIT-HUMOR Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- `lit-humor` is an active humor and satire track from burlesque and satire to postmodern parody and meme-era continuity.
- Current planning docs include `docs/l2-uk-en/LIT-HUMOR-PLAN-GENERATED.md` and active plans under `curriculum/l2-uk-en/plans/lit-humor/`.
- Primary readings can be humorous texts, satirical excerpts, parody scenes, poems, prose sketches, or documented meme/public-culture artifacts when rights allow.

## Goal

Run preflight, production, audit, or remediation for scoped `lit-humor` modules with close attention to register, satire targets, cultural context, and rights.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-humor-<stage>-<batch> .worktrees/dispatch/codex/lit-humor-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-humor-<stage>-<batch>
test -e .venv || ln -s "$REPO_ROOT/.venv" .venv
export WORKTREE_ROOT="$(pwd)"
git status --short --branch
```

## Read First

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- `docs/l2-uk-en/LIT-HUMOR-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/lit-module-template.md`
- target `curriculum/l2-uk-en/plans/lit-humor/<slug>.yaml`

## Allowed Writes

- `docs/audits/lit-humor-<scope>-<date>.md`
- scoped files under `curriculum/l2-uk-en/lit-humor/`
- `site/src/content/docs/lit-humor/<slug>.mdx`
- hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- inactive LIT remnants
- non-hostable copyrighted humor, scripts, or meme images
- protected configs, generated status/audit/review artifacts, and `data/telemetry/**`

## Lifecycle Rules

- Preflight: verify text availability, humor target, cultural context, rights, and whether a meme/public artifact can be cited or only described.
- Production: explain how humor works linguistically and politically; avoid translating the joke into dead exposition.
- Quality audit: check register, satire target, rights, and whether the module punches up rather than normalizing imperial mockery.
- Remediation: repair reading/copyright/context findings before prose polish.

## Track-Specific Checks

- Ukrainian humor should be framed as identity-preserving and power-challenging, not as provincial comic relief.
- Be careful with slurs, dialect comedy, and Soviet/Russian caricatures; quote only when pedagogically necessary and framed.

## Helpers And Headroom

Use helpers for rights checks and cultural-context verification. Compress long outputs with Headroom.

## Validation Commands

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/lit-humor").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit-humor plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Add content-generation validation for production/remediation.

## Expected Final Response

```text
LIT-HUMOR stage: <preflight | production | quality-audit | remediation>
Scope: <slugs or audit report>
Reading decisions: <summary>
Validation run: <commands and outcomes>
Forbidden artifacts included: no
swarm_used: true/false
swarm_note: <helpers used, or solo run; no swarm used>
```
