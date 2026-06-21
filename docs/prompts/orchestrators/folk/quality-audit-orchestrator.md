# FOLK Quality Audit Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- This is a post-build audit for FOLK modules, using `koliadky-shchedrivky` and `docs/folk-epic/EXEMPLAR-STANDARD.md` as the current quality bar.
- FOLK audits must inspect readings, quote provenance, source fidelity, copyright decisions, and rendered reading links.
- This audit must not modify curriculum, readings, site, plans, wiki, or source files. Its only content write is the durable report under `docs/audits/`.

## Goal

Audit built FOLK modules for seminar quality, primary readings, source grounding, quote integrity, decolonization, folk text-layer use, activity quality, vocabulary, resources, and generated/rendered output. Record every issue and propose remediation batches. Do not fix modules.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/folk-quality-audit .worktrees/dispatch/codex/folk-quality-audit origin/main
cd .worktrees/dispatch/codex/folk-quality-audit
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
- `site/src/content.config.ts`
- selected FOLK source modules, resources, plans, generated MDX, and reading files

## Allowed Writes

- `docs/audits/folk-quality-audit-<scope>-<date>.md`
- PR body or final orchestration note text for delivering the audit report

## Forbidden Writes

- curriculum source files
- site docs or reading files
- plans, wiki, dossier, source registry files
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts
- `data/telemetry/**`

## Audit Dimensions

- Reading coverage: the module surfaces the corpus-supported primary-text catalog — **FOLK floor ≥4 distinct primary readings when the gate-safe corpus holds ≥4 verified fragments** (`EXEMPLAR-STANDARD.md` §3), fewer only when the corpus genuinely lacks them and never backfilled; hosted/link-only/excerpt-only/omit decisions are explicit; scholarly works are not miscounted as readings (any `type: primary` that is actually scholarly is a finding).
- Hosted readings: valid frontmatter, `public_domain: true`, source notes, `taught_in`, and working `/readings/<slug>/` links.
- Quote integrity: no from-memory fragments; every boxed primary text has source provenance and verification status.
- Source fidelity: no ghost sources, invented collectors, unsupported dates, or citation drift.
- Decolonization: no Russocentric, Soviet, imperial, or romantic-nationalist framing errors.
- FOLK design layer: `:::primary-reading`, `:::myth-box`, `:::high-culture-bridge`, and folk activity families where evidence supports them.
- Pedagogy: seminar-style source work, close reading, comparison, and argumentation rather than encyclopedia prose.
- Validation: `verify_shippable`, generated MDX parity, reading-link integrity, VESUM/Russian-shadow outcomes when available.

## Helpers And Headroom

Use read-only helpers for quote verification, reading-link inspection, and decolonization/source review when useful. Compress long outputs with Headroom. The main orchestrator owns the final report.

## Validation Commands

Read-only or dry-run checks only:

```bash
git status --short --branch
git diff --check
.venv/bin/python scripts/readings/generate_readings.py --all-folk --dry-run --json
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

For each audited built module, run when dependencies are available:

```bash
.venv/bin/python -m scripts.build.verify_shippable folk <slug>
```

If a command writes artifacts, remove forbidden generated files before finalizing.

## Expected Final Response

```text
FOLK quality audit report: docs/audits/<file>.md
Modules audited: <slugs>
Reading findings: <summary>
Blockers: <count>
Remediation batches: <short list>
Files changed: docs/audits/<file>.md only
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
