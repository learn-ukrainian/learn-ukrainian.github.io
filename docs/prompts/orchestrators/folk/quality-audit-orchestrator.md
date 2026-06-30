# FOLK Quality Audit Orchestrator

Prompt version: 0.3
Last reviewed: 2026-06-30

## Source Assumptions

- FOLK quality audit is read-only unless an explicit remediation task follows.
- Framing is governed by `docs/folk-epic/FOLK-FRAMING-STANDARD.md` and reading coverage by `docs/folk-epic/EXEMPLAR-STANDARD.md`.
- Audit source files and rendered/generated learner pages; do not approve from source hygiene alone.
- This suite covers quality audit only for selected FOLK modules.

## Goal

Audit built FOLK modules for seminar quality, primary readings, source grounding, quote integrity, decolonization, folk text-layer use, activity quality, vocabulary, resources, and generated/rendered output. Record findings and propose remediation batches; do not fix modules.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/folk-quality-audit-<batch> .worktrees/dispatch/codex/folk-quality-audit-<batch> origin/main
cd .worktrees/dispatch/codex/folk-quality-audit-<batch>
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
- Selected FOLK audit scope
- Selected FOLK plans, source modules, generated MDX, resources, readings, activities, and vocabulary

## Allowed Writes

- `docs/audits/folk-<scope>-<date>.md` only when a durable audit report is explicitly requested
- Conversation, PR-review, and final orchestration-note findings
- No curriculum, generated MDX, reading, resource, activity, vocabulary, plan, wiki, or dossier edits in quality-audit mode

## Forbidden Writes

- FOLK plans, modules, activities, vocabulary, resources, generated MDX, readings, wiki, dossier, and source files
- `docs/prompts/orchestrators/b2/**` and unrelated track prompt suites
- Non-hostable copyrighted full texts or media under `site/src/content/readings/`
- `.python-version`, `.yamllint`, `.markdownlint.json`, package files, or linter configs
- Generated `status/`, curriculum `audit/`, curriculum `review/`, `docs/*-STATUS.md`, or `data/telemetry/**` artifacts

## Lifecycle Rules

- Read the rendered/generated page top to bottom as a student.
- Check FOLK framing standard, primary reading coverage, quote provenance, resources `role: reading`, and legal reading behavior.
- Check that no internal workflow/source labels leak into public prose.
- Check activities are correctly split between Lesson and Workbook/Activities tabs where inline practice exists.
- Check vocabulary and prose for Ukrainian fluency, no word-salad, and no English leakage outside permitted UI/glosses.

## Track-Specific Checks

- Treat FOLK framing-standard violations as blockers.
- Treat missing reading coverage or broken reading links as blockers.
- Treat invented quotes, from-memory folk text, and unverified song fragments as blockers.
- Treat a non-empty Lesson tab with an empty Workbook/Activities tab as an activity-placement blocker.

## Learner-Facing Quality And Activity Placement

- Keep build/source-verification language out of learner pages: no `prompt`, `audit`, `review`, `telemetry`, `source-tier`, `gate`, `chunk_id`, `source_chunk`, corpus/service IDs, `learner-facing`, `hosted reading`, or validation-tool language in public prose.
- Student-visible body prose should be Ukrainian unless the current page component explicitly permits English UI labels or vocabulary glosses.
- Teach through the folk material: source text, performance context, formula, variant, ritual or social function, later literary bridge, and interpretation. Do not narrate how the lesson is being built.
- If a module uses inline practice, use Activity YAML V2 with `inline:` and `workbook:` lists. Never wrap the root in an `activities:` key.
- Each `inline:` activity must have exactly one matching `<!-- INJECT_ACTIVITY: <id> -->` marker in `module.md`. Workbook activities must not have prose markers.
- The Lesson tab must not absorb the entire practice set, and the Workbook/Activities tab must not be empty.
- PR/final notes for built-module work must report `inline=<n>`, `workbook=<n>`, rendered Lesson tab status, rendered Workbook/Activities tab status, English leakage status, internal-leakage status, and an LLM-fingerprint score.

## Helpers And Headroom

Use read-only helpers for rendered-page reading, source/quote checks, copyright checks, and activity placement verification when useful. Compress long helper outputs with Headroom. The main orchestrator owns conclusions and review routing.

## Validation Commands

Read-only checks only:

```bash
git status --short --branch
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Do not run generation or build commands that write files in quality-audit mode.

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
