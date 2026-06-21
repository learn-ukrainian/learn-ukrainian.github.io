# FOLK Production Build Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- FOLK is the seminar pilot and must model reading-first seminar production.
- Every module needs a **researched primary-text catalog** — survey the corpus for every distinct verified text on the topic and surface as many as it supports (**FOLK floor: ≥4 distinct primary readings when the gate-safe corpus holds ≥4 verified fragments**, `EXEMPLAR-STANDARD.md` §3; corpus-bound, never backfilled with from-memory or scholarly-quoted text). If a text is not available, record a `reading-needed` blocker; do not build around an empty or padded reading layer.
- Hosted readings currently live in `site/src/content/readings/` and require `public_domain: true`. Non-hostable texts need `role: reading` external links and clear copyright notes.
- FOLK uses `verify_shippable` and `assemble_mdx`, not the core `generate_mdx.py` path.

## Goal

Build the selected FOLK module batch in small sequential steps. For each module, use plans, dossiers/wiki, source registries, readings, and corpus checks to write source files, readings, generated site MDX, and validation notes. Record telemetry and require independent review before merge.

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
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- `docs/folk-epic/EXEMPLAR-STANDARD.md`
- `docs/folk-epic/folk-review-rubric.md`
- `docs/folk-epic/folk-text-layer-spec.md`
- `scripts/build/phases/linear-write-seminar-folk-rules.md`
- `scripts/readings/generate_readings.py`
- `scripts/generate_mdx/reading_links.py`
- `site/src/content.config.ts`
- `curriculum/l2-uk-en/curriculum.yaml`, target FOLK modules
- for each target slug:
  - `curriculum/l2-uk-en/plans/folk/<slug>.yaml`
  - relevant dossier/wiki/source registry files
  - existing `curriculum/l2-uk-en/folk/<slug>/` files if present
  - existing `site/src/content/docs/folk/<slug>.mdx` if present
  - existing `site/src/content/readings/*.mdx` that match target readings

## Allowed Writes

- For scoped target slugs only:
  - `curriculum/l2-uk-en/folk/<slug>/module.md`
  - `curriculum/l2-uk-en/folk/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/folk/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/folk/<slug>/resources.yaml`
  - `site/src/content/docs/folk/<slug>.mdx`
  - `site/src/content/readings/<reading-slug>.mdx` only for hostable/public-domain readings
- PR body or final orchestration note text

## Forbidden Writes

- FOLK plans, wiki, dossier, or source registry files unless the user explicitly scopes a plan/source fix
- modules outside the selected batch
- non-hostable copyrighted full texts under `site/src/content/readings/`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Production Rules

- Work one module at a time. Finish reading discovery, source writing, reading generation, MDX assembly, and validation before moving to the next slug.
- Start each module from the primary reading candidates. Build the full corpus-supported catalog (FOLK target ≥4 distinct primary texts; fewer only when the gate-safe corpus genuinely lacks them, recorded as `reading-needed`). Each candidate needs a copyright decision: hosted, linked-only, excerpt-only, or omit with reason.
- Keep scholarly/secondary works (monographs, surveys, analyses) as `type: scholarly` references — never tag them `type: primary` and never count them toward the reading floor. A primary text reconstructed inside a scholar's prose is not a clean hostable reading; source the standalone text from a primary-text corpus.
- Search likely teaching/source locations such as Osvita only with exact URL and rights verification; do not invent links or assume teaching-site content is hostable.
- Use `:::primary-reading` only for verified verbatim folk-primary fragments.
- Keep archaic or dialectal forms inside quoted primary text unless VESUM/slovnyk.me/heritage verifies the form for exposition.
- Include `:::myth-box` and `:::high-culture-bridge` where evidence supports them.
- Prefer folk activity families `ritual-sequencing`, `variant-comparison`, `motif-formula`, and `performance` where the source supports them.
- Do not emit deferred audio/image surfaces such as `audio-block`, `symbolic-decode`, or `aural-genre-ID`.
- Generated site MDX must move with source edits. Assemble committed site MDX through `scripts.build.linear_pipeline.assemble_mdx`; do not hand-edit generated MDX.

## Helpers And Headroom

Use read-only explorers for reading/copyright discovery, quote/source verification, and exemplar comparison when useful. The main orchestrator owns edits. Compress long helper outputs with Headroom and include hash plus summary.

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
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
```

If `--astro-build` cannot run locally because site dependencies are unavailable, record that and rely on CI for full Astro render.

## PR, Commit, And Telemetry Requirements

- Branch: `codex/folk-production-<batch>`
- Commit trailer: `X-Agent: codex/folk-production-<batch>`
- Run `.venv/bin/python scripts/audit/lint_agent_trailer.py` before pushing.
- Persist module-build telemetry using `docs/prompts/orchestrators/shared/telemetry-and-pr.md`.
- Include `swarm_used`, `swarm_label`, `swarm_note`, reading coverage, and copyright decisions in telemetry and PR text.
- Require independent-family review before merge. Treat unresolved reading, quote, source, or decolonization findings as blockers.

## Expected Final Response

```text
FOLK modules built: <slugs>
Reading decisions: <hosted/link-only/excerpt-only/omit/needed list>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted or unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
