# LIT-HIST-FIC Orchestrator Suite

Prompt version: 0.2
Last reviewed: 2026-06-30

## Source Assumptions

- `lit-hist-fic` is an active LIT specialization track for historical fiction and memory narratives.
- Treat novel/story excerpts, author commentary, reviews, and historical source parallels as reading candidates where rights allow.
- Most modern prose is copyrighted; default to linked-only or excerpt-only unless hostable rights are explicit.
- This suite covers preflight, production, quality audit, and remediation. Use only the stage that matches the task.

## Goal

Run preflight, production, quality audit, and remediation scoped to `lit-hist-fic` modules without touching B2 or inactive LIT remnants.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-hist-fic-<stage>-<batch> .worktrees/dispatch/codex/lit-hist-fic-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-hist-fic-<stage>-<batch>
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
- `docs/l2-uk-en/templates/lit-module-template.md`
- Target plan: `curriculum/l2-uk-en/plans/lit-hist-fic/<slug>.yaml`
- Existing target source, sidecars, readings, and `site/src/content/docs/lit-hist-fic/<slug>.mdx` when present.

## Allowed Writes

- Preflight / quality audit reports under `docs/audits/lit-hist-fic-<scope>-<date>.md` when explicitly scoped.
- Scoped current-layout module files under `curriculum/l2-uk-en/lit-hist-fic/`.
- Scoped sidecars under `curriculum/l2-uk-en/lit-hist-fic/{meta,activities,vocabulary}/` when that layout is used.
- Generated learner page `site/src/content/docs/lit-hist-fic/<slug>.mdx` for scoped built modules.
- Permitted public-domain or otherwise hostable reading pages under `site/src/content/readings/`.
- PR body and final orchestration note text.

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**` and unrelated track prompt suites.
- Unrelated plans, modules, dossiers, wiki/source registries, image assets, or reading pages.
- Non-hostable copyrighted full texts or media under `site/src/content/readings/`.
- `.python-version`, `.yamllint`, `.markdownlint.json`, package files, or linter configs.
- Generated `status/`, curriculum `audit/`, curriculum `review/`, `docs/*-STATUS.md`, or `data/telemetry/**` artifacts.

## Lifecycle Rules

- Preflight: inventory source/readings availability, rights status, plan/source contradictions, and track-specific framing risks before production.
- Production: build from verified source material first, then shape lesson prose, activities, vocabulary, resources, generated MDX, and readings around that evidence.
- Quality audit: inspect source files and rendered learner pages for factual grounding, reading behavior, decolonization, English/internal leakage, activity placement, and LLM fingerprint.
- Remediation: fix source authority, rights, factuality, framing, render, and activity-split blockers before style polish.

## Track-Specific Checks

- Separate literary invention, historical source, memory politics, and authorial interpretation.
- Avoid treating fiction as historical evidence without qualification.
- Check decolonized periodization and named historical claims.

## Learner-Facing Quality And Activity Placement

- Keep build/source-verification language out of learner pages: no `prompt`, `audit`, `review`, `telemetry`, `source-tier`, `gate`, `chunk_id`, `source_chunk`, corpus/service IDs, `learner-facing`, `hosted reading`, or validation-tool language in public prose.
- Student-visible body prose should be Ukrainian unless the current track/page component explicitly permits English UI labels or vocabulary glosses.
- Teach through the subject matter: source passages, biography, historical context, literary form, performance, register, and interpretation. Do not narrate how the lesson is being built.
- For any production/remediation module that uses inline practice, use Activity YAML V2 with `inline:` and `workbook:` lists. Never wrap the root in an `activities:` key.
- Each `inline:` activity must have exactly one matching `<!-- INJECT_ACTIVITY: <id> -->` marker in `module.md`. Workbook activities must not have prose markers.
- The Lesson tab must not absorb the entire practice set, and the Workbook/Activities tab must not be empty.
- PR/final notes for built-module work must report `inline=<n>`, `workbook=<n>`, rendered Lesson tab status, rendered Workbook/Activities tab status, English leakage status, internal-leakage status, and an LLM-fingerprint score.

## Helpers And Headroom

Use one to three read-only helpers for source discovery, rights classification, rendered-page checks, leakage scoring, and track-specific framing review when useful. Compress long helper outputs with Headroom. The main orchestrator owns edits, review routing, PR creation, and merge decisions.

Independent review must be read-only and must inspect learner-facing output, source grounding, track framing, English/internal leakage, activity placement, and unresolved risks. Treat unresolved findings as blockers.

## Validation Commands

Always run for any PR:

```bash
git status --short --branch
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Parse current plans before production/remediation decisions:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml

for path in sorted(Path("curriculum/l2-uk-en/plans/lit-hist-fic").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit-hist-fic plans parse")
PY
```

Built modules also need the applicable activity, vocabulary, MDX, reading, route, site, and deterministic checks from `docs/prompts/orchestrators/shared/validation-checklist.md`. Use `.venv/bin/python`, not bare Python or `sys.executable`.

## Expected Final Response

```text
LIT-HIST-FIC stage: <preflight | production | quality-audit | remediation>
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
