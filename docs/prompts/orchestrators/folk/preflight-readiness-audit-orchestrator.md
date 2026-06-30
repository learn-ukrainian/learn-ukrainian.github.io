# FOLK Preflight Readiness Audit Orchestrator

Prompt version: 0.3
Last reviewed: 2026-06-30

## Source Assumptions

- Framing is governed by `docs/folk-epic/FOLK-FRAMING-STANDARD.md`: FOLK is a pre-literature course, Christian-heritage-first where relevant, school-canonical, and not occult/pagan-as-held-belief framing.
- FOLK modules require a researched primary-text catalog, not a token reading. Target at least four distinct corpus-verified primary texts when the corpus supports them; never backfill from memory or scholarly-quoted fragments.
- The current reading system includes `site/src/content/readings/`, `PrimaryReading`, `scripts/generate_mdx/reading_links.py`, and `scripts/readings/generate_readings.py`.
- This audit is read-only for curriculum, site, plans, wiki, and source files. The only content write is a durable report under `docs/audits/`.

## Goal

Determine whether a selected FOLK module set is ready for production or remediation. Check plans, wiki/dossier/source coverage, reading candidates, copyright decisions, quote provenance, decolonization risks, activity surfaces, and validation tooling. Do not build or fix modules.

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
- `curriculum/l2-uk-en/curriculum.yaml`
- `curriculum/l2-uk-en/plans/folk/*.yaml`
- Existing `curriculum/l2-uk-en/folk/<slug>/` source directories
- Existing `site/src/content/docs/folk/*.mdx` and `site/src/content/readings/*.mdx`

## Allowed Writes

- `docs/audits/folk-preflight-readiness-<date>.md`
- PR body and final orchestration note text delivering the audit report

## Forbidden Writes

- FOLK plans, modules, activities, vocabulary, resources, generated MDX, readings, wiki, dossier, and source files
- `.python-version`, `.yamllint`, `.markdownlint.json`, package files, or linter configs
- Generated `status/`, curriculum `audit/`, curriculum `review/`, or `data/telemetry/**` artifacts

## Audit Checks

- Apply the FOLK framing standard first: Christian-heritage-first, pre-literature identity, school-canonical sourcing, no occult/pagan-as-held-belief framing.
- Apply the school-canon validity test: if material is only material-culture / народознавство and not oral-text genre, cut or route out of FOLK.
- Verify primary-text coverage. FOLK floor is corpus-bound: at least four distinct primary texts when gate-safe corpus supports four; fewer only with recorded `reading-needed` rationale.
- Flag any `references:` entry tagged `type: primary` that is actually scholarly/secondary work.
- For every reading candidate, record copyright decision: hosted, linked-only, excerpt-only, omit, or reading-needed.
- Verify hosted readings have `site/src/content/readings/<slug>.mdx` with `public_domain: true`.
- Verify built modules have `resources.yaml` `role: reading` entries with learner tasks.
- Check `:::primary-reading` usage: no from-memory quotes, no unverified song fragments, no literary-authored verse boxed as folk.
- Check decolonization, Russian-shadow, regional variation, ghost-source, romantic-overclaim, and learner-facing leakage risks.

## Helpers And Headroom

Use one to three read-only explorers when useful for reading/copyright candidate survey, quote/source verification, or rendered/module-shape comparison. Compress helper output with Headroom when it exceeds roughly 200 lines or 20 KB. The main orchestrator writes the report and owns every conclusion.

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
Modules/plans inspected: <count slugs>
Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>
Blockers: <count>
Next production/remediation batches: <short list>
Files changed: docs/audits/<file>.md only
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
