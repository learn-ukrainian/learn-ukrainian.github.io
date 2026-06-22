# BIO Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- BIO is a seminar biography track, not C1 core. It uses source-tier dossiers, decolonization review, portrait/image-rights rules, and politically charged biography framing.
- Current source surfaces include `curriculum/l2-uk-en/plans/bio/*.yaml`, `curriculum/l2-uk-en/bio/`, `docs/audits/bio-track-gap-audit-2026-05-26.md`, `docs/best-practices/bio-research-source-tiers.md`, `docs/best-practices/bio-image-rights.md`, and `docs/best-practices/politically-charged-bios.md`.
- Every module needs primary voice readings when available: letters, poems, speeches, memoir passages, court statements, diaries, interviews, or archival documents by/about the figure.
- This suite covers preflight, production, quality audit, and remediation. Use only the stage that matches the task.

## Goal

Orchestrate BIO work in small batches without touching B2. Verify source-tier coverage, build biographies with primary readings and careful rights/framing, audit decolonization and factuality, and remediate blockers.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/bio-<stage>-<batch> .worktrees/dispatch/codex/bio-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/bio-<stage>-<batch>
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
- `docs/audits/bio-track-gap-audit-2026-05-26.md`
- `docs/audits/bio-decolonization-checklist.md`
- `docs/best-practices/bio-research-source-tiers.md`
- `docs/best-practices/bio-image-rights.md`
- `docs/best-practices/bio-naming-canonical.md`
- `docs/best-practices/politically-charged-bios.md`
- `docs/templates/bio-research-dossier-template.md`
- target `curriculum/l2-uk-en/plans/bio/<slug>.yaml`

## Allowed Writes

- Preflight or quality audit: `docs/audits/bio-<scope>-<date>.md`
- For scoped BIO target slugs only:
  - current-layout source files under `curriculum/l2-uk-en/bio/`
  - `site/src/content/docs/bio/<slug>.mdx`
  - hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- unrelated BIO plans, dossiers, modules, or image assets
- non-hostable copyrighted full text or images
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: verify Tier 1/Tier 2 source packs, primary voice readings, portrait rights or fallback, and content-warning fields for politically charged figures.
- Production: foreground Ukrainian agency and the specific oppression mechanism; cite narrow, not broad; include primary voice when legally usable.
- Quality audit: run the decolonization checklist, source-tier audit, naming/transliteration check, portrait-rights check, and reading-link/copyright review.
- Remediation: fix source authority and framing blockers before prose polish.

## Track-Specific Checks

- Russian/Soviet sources are historical evidence, not authority over Ukrainian identity or motives.
- Do not write hagiography. Name documented contested ideology, civilian harm, collaboration allegations, or memory disputes with sourced precision.
- For recent war-killed or captivity figures, avoid re-victimizing images or propaganda-origin material.

## Helpers And Headroom

Use read-only helpers for source-tier packets, image-rights checks, and politically charged framing review. Compress long findings with Headroom.

## Validation Commands

Adapt to current target layout:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/bio").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("bio plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

For built modules, add activity, vocabulary, generated MDX, liveness, and site checks from `shared/validation-checklist.md`.

## Expected Final Response

```text
BIO stage: <preflight | production | quality-audit | remediation>
Scope: <slugs or audit report>
Source-tier coverage: <summary>
Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>
Portrait rights: <hosted/link-only/omit/needed counts>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted | not module-build | unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
