# FOLK Remediation Build Orchestrator

Prompt version: 0.3
Last reviewed: 2026-06-30

## Source Assumptions

- Framing is governed by `docs/folk-epic/FOLK-FRAMING-STANDARD.md`; framing fixes are first-class remediations.
- This prompt consumes durable FOLK audit findings and fixes source grounding, readings, quote integrity, copyright, rendered links, and seminar pedagogy in small PR-sized batches.
- Do not turn FOLK into a generic core-language lesson. Preserve seminar source work and the folk text layer.
- Public learner pages may show public source names/URLs and Ukrainian academic reading habits, but not validation workflow labels.

## Goal

Fix selected FOLK audit findings without changing unrelated modules. Include reading/copyright fixes, `resources.yaml` `role: reading` repair, hosted reading updates when permitted, source module fixes, generated MDX updates, validation, telemetry, and independent review.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/folk-remediation-<batch> .worktrees/dispatch/codex/folk-remediation-<batch> origin/main
cd .worktrees/dispatch/codex/folk-remediation-<batch>
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
- **`docs/folk-epic/FOLK-FRAMING-STANDARD.md` (read first; non-negotiable framing standard)**
- `docs/folk-epic/EXEMPLAR-STANDARD.md`
- `docs/folk-epic/folk-review-rubric.md`
- `docs/folk-epic/folk-text-layer-spec.md`
- `scripts/build/phases/linear-write-seminar-folk-rules.md`
- `site/src/content.config.ts`
- `scripts/readings/generate_readings.py`
- Selected FOLK audit report under `docs/audits/`
- Affected FOLK plans, modules, resources, activities, vocabulary, generated MDX, and reading files

## Allowed Writes

- Scoped `curriculum/l2-uk-en/folk/<slug>/module.md`
- Scoped `curriculum/l2-uk-en/folk/<slug>/activities.yaml`
- Scoped `curriculum/l2-uk-en/folk/<slug>/vocabulary.yaml`
- Scoped `curriculum/l2-uk-en/folk/<slug>/resources.yaml`
- Generated `site/src/content/docs/folk/<slug>.mdx`
- Permitted public-domain or otherwise hostable reading pages under `site/src/content/readings/`
- PR body and final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**` and unrelated track prompt suites
- Unrelated FOLK modules, plans, wiki, dossier, source registries, image assets, or reading pages unless explicitly scoped by the audit batch
- Non-hostable copyrighted full text under `site/src/content/readings/`
- `.python-version`, `.yamllint`, `.markdownlint.json`, package files, or linter configs
- Generated `status/`, curriculum `audit/`, curriculum `review/`, `docs/*-STATUS.md`, or `data/telemetry/**` artifacts

## Lifecycle Rules

- Fix FOLK framing-standard violations before prose polish.
- Fix reading deficits and `resources.yaml role: reading` issues before activity polish.
- Re-tag secondary/scholarly works correctly; never count them toward the primary reading floor.
- Assemble committed site MDX through `scripts.build.linear_pipeline.assemble_mdx`; do not hand-edit generated MDX except for a documented emergency.
- Re-run source/quote/decolonization checks after edits.

## Track-Specific Checks

- Treat reading/copyright findings as first-class remediation, not optional cleanup.
- Preserve verified archaic/dialectal forms inside quoted primary text; verify exposition forms with current source tools.
- Do not expose build workflow language in public prose.
- Independent review must read the rendered/generated learner page, not only source files.

## Learner-Facing Quality And Activity Placement

- Keep build/source-verification language out of learner pages: no `prompt`, `audit`, `review`, `telemetry`, `source-tier`, `gate`, `chunk_id`, `source_chunk`, corpus/service IDs, `learner-facing`, `hosted reading`, or validation-tool language in public prose.
- Student-visible body prose should be Ukrainian unless the current page component explicitly permits English UI labels or vocabulary glosses.
- Teach through the folk material: source text, performance context, formula, variant, ritual or social function, later literary bridge, and interpretation. Do not narrate how the lesson is being built.
- If a module uses inline practice, use Activity YAML V2 with `inline:` and `workbook:` lists. Never wrap the root in an `activities:` key.
- Each `inline:` activity must have exactly one matching `<!-- INJECT_ACTIVITY: <id> -->` marker in `module.md`. Workbook activities must not have prose markers.
- The Lesson tab must not absorb the entire practice set, and the Workbook/Activities tab must not be empty.
- PR/final notes for built-module work must report `inline=<n>`, `workbook=<n>`, rendered Lesson tab status, rendered Workbook/Activities tab status, English leakage status, internal-leakage status, and an LLM-fingerprint score.

## Helpers And Headroom

Use read-only helpers for reading source search, copyright classification, source/quote verification, rendered-page checks, and activity placement verification when useful. Compress long helper outputs with Headroom. The main agent owns edits and integration.

## Validation Commands

Adapt slugs and paths:

```bash
.venv/bin/python scripts/readings/generate_readings.py curriculum/l2-uk-en/folk/<slug> --dry-run --json
SLUG="<slug>" .venv/bin/python - <<'PY'
import os
from pathlib import Path
from scripts.build.linear_pipeline import assemble_mdx

slug = os.environ["SLUG"]
assemble_mdx(
    Path("curriculum/l2-uk-en/folk") / slug,
    Path("site/src/content/docs/folk") / f"{slug}.mdx",
    Path("curriculum/l2-uk-en/plans/folk") / f"{slug}.yaml",
)
PY
.venv/bin/python -m scripts.build.verify_shippable folk <slug>
.venv/bin/python -m scripts.build.verify_shippable folk <slug> --astro-build
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

If `--astro-build` cannot run locally because site dependencies are unavailable, record the reason and require CI.

## Expected Final Response

```text
FOLK stage: <preflight | production | quality-audit | remediation>
Scope: <slugs or audit report>
Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>
Activity split: <inline=n, workbook=n, rendered lesson/workbook status or not applicable>
Quality score: <LLM fingerprint, English leakage, internal leakage, unresolved blockers>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted | not module-build | unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
