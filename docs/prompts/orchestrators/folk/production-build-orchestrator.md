# FOLK Production Build Orchestrator

Prompt version: 0.3
Last reviewed: 2026-06-30

## Source Assumptions

- Framing is governed by `docs/folk-epic/FOLK-FRAMING-STANDARD.md`; framing violations are build blockers.
- FOLK production is reading-first seminar production built from a researched primary-text catalog.
- Hosted readings under `site/src/content/readings/` require `public_domain: true`; non-hostable texts need link-only or excerpt-only handling with clear learner tasks.
- FOLK uses `verify_shippable` and `scripts.build.linear_pipeline.assemble_mdx`, not the core `generate_mdx.py` path.

## Goal

Build selected FOLK modules from verified primary readings, source-grounded framing, legal reading surfaces, activities, vocabulary, resources, generated MDX, telemetry, and independent review.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/folk-production-<batch> .worktrees/dispatch/codex/folk-production-<batch> origin/main
cd .worktrees/dispatch/codex/folk-production-<batch>
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
- Target plan: `curriculum/l2-uk-en/plans/folk/<slug>.yaml`
- Relevant dossier/wiki/source registry files
- Existing `curriculum/l2-uk-en/folk/<slug>/` files if present
- Existing `site/src/content/docs/folk/<slug>.mdx` and readings when present

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
- Unrelated FOLK plans, modules, dossiers, wiki/source registries, image assets, or reading pages
- Non-hostable copyrighted full texts or media under `site/src/content/readings/`
- `.python-version`, `.yamllint`, `.markdownlint.json`, package files, or linter configs
- Generated `status/`, curriculum `audit/`, curriculum `review/`, `docs/*-STATUS.md`, or `data/telemetry/**` artifacts

## Lifecycle Rules

- Start from primary reading candidates and copyright decisions: hosted, linked-only, excerpt-only, omit, or reading-needed.
- Keep scholarly/secondary works as `type: scholarly`; never count them toward the primary reading floor.
- Use `:::primary-reading` only for verified verbatim folk-primary fragments.
- Include `:::myth-box`, `:::high-culture-bridge`, and folk activity families where evidence supports them.
- Generated site MDX must move with source edits; assemble committed MDX through `scripts.build.linear_pipeline.assemble_mdx`.

## Track-Specific Checks

- Apply `FOLK-FRAMING-STANDARD.md` before writing: Christian-heritage-first where relevant, pre-literature identity, school-canonical sourcing, and no occult/pagan-as-held-belief framing.
- Verify at least four distinct primary readings when gate-safe corpus supports four; fewer only with recorded `reading-needed` rationale.
- Do not emit deferred audio/image surfaces unless the current implementation supports them.
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

Use read-only helpers for reading/copyright discovery, quote/source verification, rendered-page checking, and exemplar comparison when useful. Compress long helper outputs with Headroom. The main orchestrator owns edits, review routing, PR creation, and merge decisions.

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
