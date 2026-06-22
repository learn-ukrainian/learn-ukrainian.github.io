# LIT-FANTASTIKA Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- `lit-fantastika` is an active speculative fiction track covering Gothic, fantasy, science fiction, magical realism, cyberpunk, and mythic fiction.
- Current planning docs include `docs/l2-uk-en/LIT-FANTASTIKA-PLAN-GENERATED.md` and active plans under `curriculum/l2-uk-en/plans/lit-fantastika/`.
- Many texts are modern and copyrighted; default to linked-only or excerpt-only unless public-domain/hostable status is verified.

## Goal

Run preflight, production, audit, or remediation for scoped `lit-fantastika` modules, with primary readings and genre analysis that frames Ukrainian speculative fiction as its own tradition.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-fantastika-<stage>-<batch> .worktrees/dispatch/codex/lit-fantastika-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-fantastika-<stage>-<batch>
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
- `docs/l2-uk-en/LIT-FANTASTIKA-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/lit-module-template.md`
- target `curriculum/l2-uk-en/plans/lit-fantastika/<slug>.yaml`

## Allowed Writes

- `docs/audits/lit-fantastika-<scope>-<date>.md`
- scoped files under `curriculum/l2-uk-en/lit-fantastika/`
- `site/src/content/docs/lit-fantastika/<slug>.mdx`
- hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- inactive LIT remnants
- non-hostable copyrighted contemporary fiction
- protected configs, generated status/audit/review artifacts, and `data/telemetry/**`

## Lifecycle Rules

- Preflight: verify text availability, rights, genre context, and whether the work is public-domain, linked-only, or excerpt-only.
- Production: analyze genre devices, Ukrainian mythic/cultural context, and anti-imperial stakes without reducing the work to plot summary.
- Quality audit: check genre claims, source identity, rights, and avoidance of "derivative of Russian sci-fi" framing.
- Remediation: repair source, reading, and copyright findings first.

## Track-Specific Checks

- Berdnyk/dissident or Soviet-era texts need political context and source verification.
- Contemporary genre fiction must be handled with careful copyright limits.

## Helpers And Headroom

Use helpers for rights and text-location checks. Compress long source surveys with Headroom.

## Validation Commands

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/lit-fantastika").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit-fantastika plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Add content-generation validation for production/remediation.

## Expected Final Response

```text
LIT-FANTASTIKA stage: <preflight | production | quality-audit | remediation>
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
