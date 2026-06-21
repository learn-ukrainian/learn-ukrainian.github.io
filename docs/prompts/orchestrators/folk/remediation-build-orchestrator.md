# FOLK Remediation Build Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- This prompt consumes a durable FOLK audit report under `docs/audits/`.
- FOLK remediation fixes source-grounding, readings, quote integrity, copyright, rendered links, and seminar pedagogy in small PR-sized batches.
- Do not turn FOLK into a generic core-language lesson. Preserve seminar source work and the folk text layer.

## Goal

Fix all selected FOLK audit findings without changing unrelated modules. Include reading/copyright fixes, `resources.yaml` `role: reading` repair, hosted reading updates when permitted, source module fixes, generated MDX updates, validation, telemetry, and independent review.

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
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- selected FOLK audit report under `docs/audits/`
- `docs/folk-epic/EXEMPLAR-STANDARD.md`
- `docs/folk-epic/folk-review-rubric.md`
- affected FOLK plans, source modules, resources, activities, vocabulary, generated MDX, and reading files

## Allowed Writes

- For scoped target slugs and readings only:
  - `curriculum/l2-uk-en/folk/<slug>/module.md`
  - `curriculum/l2-uk-en/folk/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/folk/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/folk/<slug>/resources.yaml`
  - `site/src/content/docs/folk/<slug>.mdx`
  - `site/src/content/readings/<reading-slug>.mdx` when hosting is legally permitted
- PR body or final orchestration note text

## Forbidden Writes

- unrelated FOLK modules
- non-hostable copyrighted full text under `site/src/content/readings/`
- FOLK plans, wiki, dossier, or source registries unless explicitly scoped by the audit batch
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Remediation Rules

- Every audit finding selected for the batch must be fixed or explicitly deferred with reason.
- Reading findings are first-class: fix missing `role: reading`, broken `/readings/` links, missing hosted files, bad copyright decisions, and missing learner tasks before declaring the module clean.
- **Reading-deficit findings are first-class too:** when the gate-safe corpus holds ≥4 distinct verified primary texts but the module surfaces fewer (FOLK floor, `EXEMPLAR-STANDARD.md` §3), add the missing texts from the corpus — never backfill with from-memory, paraphrased, or scholarly-quoted content. Re-tag any `type: primary` reference that is actually a secondary/scholarly work as `type: scholarly`; it does not count toward the floor.
- For unavailable texts, record the search and leave a visible reading-needed blocker instead of hiding the gap.
- If hosting is not permitted, use link-only or excerpt-only treatment; do not paste full copyrighted text.
- Regenerate readings and module MDX through current repo tooling; do not hand-edit generated output except with a documented reason. Assemble committed site MDX through `scripts.build.linear_pipeline.assemble_mdx`.
- Re-run source/quote/decolonization checks after edits.

## Helpers And Headroom

Use read-only helpers for reading source search, copyright classification, and source/quote verification when useful. Main agent owns edits and integration. Compress long helper output with Headroom.

## Validation Commands

Adapt slugs:

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
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

If `--astro-build` is unavailable locally, record the reason and require CI.

## PR, Commit, And Telemetry Requirements

- Branch: `codex/folk-remediation-<batch>`
- Commit trailer: `X-Agent: codex/folk-remediation-<batch>`
- Persist module-build/remediation telemetry using `docs/prompts/orchestrators/shared/telemetry-and-pr.md`.
- PR body must include audit findings addressed, reading decisions, validation, independent review, and forbidden-artifact confirmation.
- Require independent-family review before merge.

## Expected Final Response

```text
FOLK audit report used: <path>
Findings fixed: <ids/count>
Reading decisions changed: <summary>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted or unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
