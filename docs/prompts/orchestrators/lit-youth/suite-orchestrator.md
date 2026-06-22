# LIT-YOUTH Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- `lit-youth` is the active children's and young-adult literature track. Older planning docs may call this area `LIT-JUVENILE`; do not create a separate stale track from that name.
- Current planning docs include `docs/l2-uk-en/LIT-JUVENILE-PLAN-GENERATED.md` and active plans under `curriculum/l2-uk-en/plans/lit-youth/`.
- Most modern children's/YA texts are copyrighted. Use linked-only or excerpt-only unless hostable rights are verified.

## Goal

Run preflight, production, quality audit, or remediation for scoped `lit-youth` modules with age-aware text selection, rights discipline, and seminar-level literary analysis.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-youth-<stage>-<batch> .worktrees/dispatch/codex/lit-youth-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-youth-<stage>-<batch>
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
- `docs/l2-uk-en/LIT-JUVENILE-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/lit-module-template.md`
- target `curriculum/l2-uk-en/plans/lit-youth/<slug>.yaml`

## Allowed Writes

- `docs/audits/lit-youth-<scope>-<date>.md`
- scoped files under `curriculum/l2-uk-en/lit-youth/`
- `site/src/content/docs/lit-youth/<slug>.mdx`
- hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- a separate `lit-juvenile`, `lit-doc`, or `lit-crimea` prompt suite
- non-hostable full children's/YA texts or illustrations
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: verify text availability, rights, active naming (`lit-youth`), age/register suitability, and reading links.
- Production: analyze how children's/YA literature builds Ukrainian language, imagination, and identity without flattening it into simple reading practice.
- Quality audit: check rights, age-aware framing, literary depth, and no patronizing tone.
- Remediation: repair rights and reading blockers before prose polish.

## Track-Specific Checks

- Do not host illustrations or full modern books without explicit rights.
- Keep practical value for bilingual families visible when the plan supports it, but preserve seminar analysis.

## Helpers And Headroom

Use helpers for rights checks and text availability. Compress long outputs with Headroom.

## Validation Commands

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/lit-youth").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit-youth plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Add content-generation validation for production/remediation.

## Expected Final Response

```text
LIT-YOUTH stage: <preflight | production | quality-audit | remediation>
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
