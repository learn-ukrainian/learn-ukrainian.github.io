# OES Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- OES is the Old Rus' / early Ukrainian historical-linguistic seminar track for
  the X-XIII century. It is not B2, not HIST, and not a generic medieval culture
  track.
- Current sources include `curriculum/l2-uk-en/plans/oes/*.yaml`,
  `curriculum/l2-uk-en/oes/`, `site/src/content/docs/oes/`,
  `docs/archive/OES-CURRICULUM.md`, and relevant linguistic/source references.
- Every module needs a source-reading catalog: inscriptions, graffiti, birch
  bark letters, chronicle passages, legal texts, sermons, or literary excerpts,
  classified by hosting rights. If a text is unavailable or rights are unclear,
  record `reading-needed`; do not omit the reading layer.
- This suite covers preflight, production, quality audit, and remediation. Use
  only the stage that matches the task.

## Goal

Orchestrate OES batches without touching B2. Build modules around verified
source passages, historical phonology, orthography, paleography, register, and
decolonized terminology.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/oes-<stage>-<batch> .worktrees/dispatch/codex/oes-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/oes-<stage>-<batch>
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
- `docs/archive/OES-CURRICULUM.md`
- target `curriculum/l2-uk-en/plans/oes/<slug>.yaml`
- existing target source, sidecars, readings, and
  `site/src/content/docs/oes/<slug>.mdx` when present

## Allowed Writes

- Preflight or quality audit: `docs/audits/oes-<scope>-<date>.md`
- For scoped OES target slugs only:
  - current-layout source files under `curriculum/l2-uk-en/oes/`
  - sidecars under `curriculum/l2-uk-en/oes/{meta,activities,vocabulary}/`
    when the current layout uses them
  - `site/src/content/docs/oes/<slug>.mdx`
  - hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- HIST, ISTORIO, or RUTH modules unless the task explicitly scopes cross-track
  remediation
- plans, textbook references, wiki/source registries, or unrelated tracks unless
  explicitly scoped
- non-hostable copyrighted full texts under `site/src/content/readings/`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and
  `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: identify the exact source passage, edition/transcription status,
  register, paleographic notes, rights status, and linguistic feature focus
  before production.
- Production: anchor prose and tasks in primary-source analysis before
  historical explanation; every archaic form needs a source-backed reading and a
  modern-Ukrainian learning purpose.
- Quality audit: verify quoted forms, orthography, transliteration,
  phonological claims, register labels, and decolonized terminology.
- Remediation: fix source passage, terminology, and quote/orthography findings
  before style or activity polish.

## Track-Specific Checks

- Use the track's Old Rus' / Old Ukrainian terminology and avoid imperial or
  uniform-language framing.
- Distinguish high/literary, legal, and vernacular registers instead of
  flattening them into one medieval language.
- Typical source families include St Sophia graffiti, birch bark letters,
  Povist vremennykh lit, Ruska Pravda, sermons, hagiography, and Slovo o polku
  Ihorevim.
- Do not modernize, normalize, or silently repair source spelling inside
  verbatim examples.

## Helpers And Headroom

Use helpers for source passage discovery, edition comparison, and terminology
review. Compress long source tables or transcription comparisons with Headroom.

## Validation Commands

Adapt to current target layout:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/oes").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("oes plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

For built modules, add the current sidecar, MDX, reading, and site validation
commands from `shared/validation-checklist.md`.

## Expected Final Response

```text
OES stage: <preflight | production | quality-audit | remediation>
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
