# RUTH Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- RUTH is the Ruthenian / Middle Ukrainian historical-linguistic seminar track
  for the XIV-XVIII century. It follows OES conceptually but must stand on its
  own source evidence.
- Current sources include `curriculum/l2-uk-en/plans/ruth/*.yaml`,
  `curriculum/l2-uk-en/ruth/`, `site/src/content/docs/ruth/`,
  `docs/archive/RUTH-CURRICULUM.md`, and relevant linguistic/source references.
- Every module needs a source-reading catalog: legal, chancery, scriptural,
  grammatical, lexicographic, polemical, chronicle, constitutional, or
  philosophical texts, classified by hosting rights. If a text is unavailable or
  rights are unclear, record `reading-needed`; do not omit the reading layer.
- This suite covers preflight, production, quality audit, and remediation. Use
  only the stage that matches the task.

## Goal

Orchestrate RUTH batches without touching B2. Build modules around verified
Ruthenian and Prosta Mova source passages, diglossia, chancery style, baroque
registers, and decolonized historical-linguistic framing.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/ruth-<stage>-<batch> .worktrees/dispatch/codex/ruth-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/ruth-<stage>-<batch>
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
- `docs/archive/RUTH-CURRICULUM.md`
- target `curriculum/l2-uk-en/plans/ruth/<slug>.yaml`
- existing target source, sidecars, readings, and
  `site/src/content/docs/ruth/<slug>.mdx` when present

## Allowed Writes

- Preflight or quality audit: `docs/audits/ruth-<scope>-<date>.md`
- For scoped RUTH target slugs only:
  - current-layout source files under `curriculum/l2-uk-en/ruth/`
  - sidecars under `curriculum/l2-uk-en/ruth/{meta,activities,vocabulary}/`
    when the current layout uses them
  - `site/src/content/docs/ruth/<slug>.mdx`
  - hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- OES, HIST, or ISTORIO modules unless the task explicitly scopes cross-track
  remediation
- plans, textbook references, wiki/source registries, or unrelated tracks unless
  explicitly scoped
- non-hostable copyrighted full texts under `site/src/content/readings/`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and
  `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: identify the exact source passage, edition/transcription status,
  register, rights status, historical context, and linguistic feature focus
  before production.
- Production: anchor prose and tasks in primary-source reading before broader
  historical explanation; every archaic or mixed-register form needs a
  source-backed reading and a modern-Ukrainian learning purpose.
- Quality audit: verify quoted forms, orthography, translation/gloss choices,
  register labels, historical claims, and decolonized terminology.
- Remediation: fix source passage, terminology, and quote/orthography findings
  before style or activity polish.

## Track-Specific Checks

- Distinguish Ruthenian, Prosta Mova, Church Slavonic, Polish, Latin, and modern
  Ukrainian layers instead of flattening them.
- Typical source families include Lithuanian Statutes, Peresopnytsia Gospel,
  Ostrih Bible, Smotrytsky grammar, Berynda lexicon, polemical prose, Cossack
  chronicles, Orlyk's Constitution, and Skovoroda.
- Treat chancery formulae, legal vocabulary, diglossia, orthography, and
  paleography as factual content requiring source support.
- Do not modernize, normalize, or silently repair source spelling inside
  verbatim examples.

## Helpers And Headroom

Use helpers for source passage discovery, edition comparison, rights
classification, and terminology review. Compress long source tables or
transcription comparisons with Headroom.

## Validation Commands

Adapt to current target layout:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/ruth").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("ruth plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

For built modules, add the current sidecar, MDX, reading, and site validation
commands from `shared/validation-checklist.md`.

## Expected Final Response

```text
RUTH stage: <preflight | production | quality-audit | remediation>
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
