# FOLK Preflight Readiness Audit Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- FOLK is the pilot seminar track. Use it to establish patterns for later seminar tracks, but verify every rule against the current repo.
- FOLK modules require a researched primary-text catalog, not a single token reading — target ≥4 distinct corpus-verified primary texts per module when the corpus supports it (`EXEMPLAR-STANDARD.md` §3), corpus-bound and never backfilled. If readings are not yet available, record blockers/reading-needed tasks rather than omitting them.
- The current reading system includes `site/src/content/readings/`, `PrimaryReading`, `scripts/generate_mdx/reading_links.py`, and `scripts/readings/generate_readings.py`.
- This audit is read-only for curriculum, site, plans, wiki, and source files. Its only content write is a durable report under `docs/audits/`.

## Goal

Determine whether the selected FOLK module set is ready for production or remediation. Check plans, wiki/dossier/source coverage, reading candidates, copyright decisions, quote provenance, decolonization risks, activity surfaces, and validation tooling. Do not build or fix modules.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/folk-preflight-readiness .worktrees/dispatch/codex/folk-preflight-readiness origin/main
cd .worktrees/dispatch/codex/folk-preflight-readiness
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
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- `docs/folk-epic/EXEMPLAR-STANDARD.md`
- `docs/folk-epic/folk-review-rubric.md`
- `docs/folk-epic/folk-text-layer-spec.md`
- `scripts/build/phases/linear-write-seminar-folk-rules.md`
- `site/src/content.config.ts`
- `scripts/readings/generate_readings.py`
- `curriculum/l2-uk-en/curriculum.yaml`
- `curriculum/l2-uk-en/plans/folk/*.yaml`
- existing `curriculum/l2-uk-en/folk/<slug>/` source directories
- existing `site/src/content/docs/folk/*.mdx`
- existing `site/src/content/readings/*.mdx`

## Allowed Writes

- `docs/audits/folk-preflight-readiness-<date>.md`
- PR body or final orchestration note text for delivering the audit report

## Forbidden Writes

- FOLK plans, modules, activities, vocabulary, resources, generated MDX, readings, wiki, dossier, or source files
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts
- `data/telemetry/**`

## Audit Checks

- Confirm active FOLK track shape from current source/site files; do not infer active tracks from plan-only leftovers.
- For every selected plan, survey corpus/source availability and report the **primary-text catalog**: how many distinct verified primary texts the corpus holds for the topic vs how many the plan/module currently surfaces. Raise a **reading-deficit** finding when the corpus supports ≥4 distinct texts but the plan/module surfaces fewer (FOLK floor, `EXEMPLAR-STANDARD.md` §3); raise `reading-needed` when no usable text exists. The floor is corpus-bound — fewer than 4 is acceptable only when the gate-safe corpus genuinely lacks that many distinct verified texts, and is **never** met by backfilled or scholarly-quoted text.
- Flag any `references:` entry tagged `type: primary` that is actually a secondary/scholarly work (monograph, survey, analysis, e.g. Костомаров/Чижевський/Попович); these must be `type: scholarly` and must not count toward the reading floor.
- For every reading candidate, record copyright decision: hosted, linked-only, excerpt-only, or omit.
- Verify that hosted readings have or need `site/src/content/readings/<slug>.mdx` with `public_domain: true`.
- Verify that each built module has `resources.yaml` with one or more `role: reading` entries and learner tasks.
- Check `:::primary-reading` usage against the exemplar: no from-memory quotes, no unverified song fragments, no literary-authored verse boxed as folk.
- Check decolonization, Russian-shadow, regional variation, ghost-source, and romantic-overclaim risks.
- Check FOLK text-layer expectations: `:::myth-box`, `:::high-culture-bridge`, and folk activity families where evidence supports them.

## Helpers And Headroom

Use one to three read-only explorers when useful:

- reading/copyright candidate survey
- quote/source/dossier verification
- rendered/module-shape comparison against `koliadky-shchedrivky`

Compress helper output with Headroom when it exceeds roughly 200 lines or 20 KB. The main orchestrator writes the report and owns every conclusion.

## Validation Commands

Read-only checks only:

```bash
git status --short --branch
git diff --check
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/folk").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("folk plans parse")
PY
.venv/bin/python scripts/readings/generate_readings.py --all-folk --dry-run --json
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Do not run build or generation commands that write files in this audit.

## Expected Final Response

```text
FOLK preflight report: docs/audits/<file>.md
Modules/plans inspected: <count and slugs>
Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>
Blockers: <count>
Next production/remediation batches: <short list>
Files changed: docs/audits/<file>.md only
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
