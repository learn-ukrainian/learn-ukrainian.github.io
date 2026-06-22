# LIT Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- LIT is the main Ukrainian literature seminar track. It is distinct from C1/C2 literature modules and from active `lit-*` specialization tracks.
- Current sources include `curriculum/l2-uk-en/plans/lit/*.yaml`, `curriculum/l2-uk-en/lit/`, `docs/l2-uk-en/LIT-PLAN-GENERATED.md`, `docs/l2-uk-en/templates/lit-module-template.md`, `docs/audits/bio-lit-cross-reference-exclusions.md`, and literary textbook references.
- Every module needs a primary literary reading catalog: works, excerpts, poems, letters, diaries, or authorial texts, classified by hosting rights.
- This suite covers preflight, production, quality audit, and remediation. Use only the stage that matches the task.

## Goal

Orchestrate LIT work without touching B2 or stale `lit-crimea` / `lit-doc` plan-only remnants. Build literary seminar modules around verified Ukrainian-language primary texts, decolonized literary history, and source-grounded analysis.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-<stage>-<batch> .worktrees/dispatch/codex/lit-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-<stage>-<batch>
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
- `docs/l2-uk-en/LIT-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/lit-module-template.md`
- `docs/audits/bio-lit-cross-reference-exclusions.md`
- `docs/audits/bio-lit-cross-reference-gaps.md`
- target `curriculum/l2-uk-en/plans/lit/<slug>.yaml`
- existing target source, sidecars, readings, and `site/src/content/docs/lit/<slug>.mdx` when present

## Allowed Writes

- Preflight or quality audit: `docs/audits/lit-<scope>-<date>.md`
- For scoped LIT target slugs only:
  - current-layout source files under `curriculum/l2-uk-en/lit/`
  - sidecars under `curriculum/l2-uk-en/lit/{meta,activities,vocabulary}/` when the current layout uses them
  - `site/src/content/docs/lit/<slug>.mdx`
  - hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- `docs/prompts/orchestrators/lit-crimea/**` or `docs/prompts/orchestrators/lit-doc/**`
- plan-only stale `lit-crimea` / `lit-doc` work unless current manifests restore them
- non-hostable copyrighted full literary texts
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: verify active LIT taxonomy, primary text availability, copyright, sidecar layout, and LIT/BIO cross-reference implications.
- Production: start from primary texts and the literary question; lecture prose, vocabulary, and activities must support close reading and argument.
- Quality audit: check quote fidelity, Ukrainian literary independence, no Russian/Soviet critical framing as authority, no invented publication facts.
- Remediation: repair reading/copyright/source issues before style or activity polish.

## Track-Specific Checks

- Ukrainian literature is an independent European tradition, not a branch of Russian letters.
- Ukrainian-language authors only unless the plan explicitly frames translation, multilingual context, or imperial language politics.
- Do not copy reference modules verbatim; use them as research scaffolding only.

## Helpers And Headroom

Use helpers for text availability, copyright classification, and quote verification. Compress long source surveys with Headroom.

## Validation Commands

Adapt to current target layout:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/lit").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

For built modules, add the current LIT sidecar, MDX, and site validation commands from `shared/validation-checklist.md`.

## Expected Final Response

```text
LIT stage: <preflight | production | quality-audit | remediation>
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
