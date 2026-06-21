# A1 Quality Audit Orchestrator

Prompt version: 0.1
Last reviewed: 2026-06-21

## Source Assumptions

- A1 is the beginner track. Do not judge it by B1 or B2 immersion habits.
- Current repo examples show A1 uses English support, short Ukrainian chunks, stress marks, letter/sound work, and warm repair language.
- Thresholds and stress/pronunciation rules must be verified from `scripts/config.py`, `scripts/audit/config.py`, and current docs before judging.
- This audit is read-only except for the durable report under `docs/audits/`.

## Goal

Audit A1 modules for beginner-safe pedagogy, emotional safety, scaffolding, Cyrillic/decodability, pronunciation support, activity quality, vocabulary usefulness, and source/wiki coverage. Record every issue found and propose remediation batches. Do not fix modules.

## WORKTREE_ROOT Setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/a1-quality-audit .worktrees/dispatch/codex/a1-quality-audit origin/main
cd .worktrees/dispatch/codex/a1-quality-audit
test -e .venv || ln -s /Users/krisztiankoos/projects/learn-ukrainian/.venv .venv
export WORKTREE_ROOT="/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-quality-audit"
pwd
git status --short --branch
git rev-parse --show-toplevel
```

All commands must run from `WORKTREE_ROOT`.

## Read First

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `curriculum/l2-uk-en/curriculum.yaml`, A1 section
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `docs/runbooks/module-build-token-telemetry.md`
- `scripts/config.py`
- `scripts/audit/config.py`
- `docs/best-practices/ulp-presentation-pattern.md` if present
- representative A1 files before expanding scope:
  - `curriculum/l2-uk-en/a1/sounds-letters-and-hello/module.md`
  - `curriculum/l2-uk-en/a1/reading-ukrainian/module.md`
  - `curriculum/l2-uk-en/a1/special-signs/module.md`
  - `curriculum/l2-uk-en/a1/my-morning/module.md`
  - `curriculum/l2-uk-en/a1/a1-finale/module.md`
  - matching `activities.yaml`, `vocabulary.yaml`, `resources.yaml`, plans, wiki files under `wiki/pedagogy/a1/`, and site MDX under `site/src/content/docs/a1/`

## Allowed Writes

- `docs/audits/a1-quality-audit-YYYY-MM-DD.md`

## Forbidden Writes

- `curriculum/l2-uk-en/**`
- `site/src/content/docs/**`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- any `status/`, curriculum `audit/`, or curriculum `review/` artifact

## Audit Checks

- Verify A1 module order, module numbers, and groups from `curriculum.yaml`.
- Verify current A1 word targets, immersion bands, grammar constraints, activity thresholds, and stress/pronunciation policy from code and current docs before judging.
- Check beginner emotional safety: no shaming, no "you should already know", repair language is calm, and failure states are framed as orientation.
- Check scaffolding: each new idea moves from sound/word/chunk to sentence; tables and examples do not assume unseen grammar.
- Check Cyrillic and decodability: early modules explain sound vs letter, syllable counting, `ь`, apostrophe, `я/ю/є/ї`, and avoid transliteration except where current repo policy allows it.
- Check stress and pronunciation support: stress marks follow current repo policy; pronunciation traps are handled with simple, actionable routines.
- Check cognitive load: sentence length, number of new concepts per section, and activity item complexity fit A1.
- Check English/Ukrainian balance against the current A1 immersion bands, not a flat percentage.
- Check activities: enough practice variety, inline/workbook split where present, no content trivia masquerading as language practice.
- Check vocabulary: beginner-useful words, examples with stress where current policy requires it, no unexplained overload.
- Check engagement: warm examples, micro-dialogues, real A1 situations, and Ukrainian-first moments where safe.
- Check plan/wiki/source coverage against the A1 plan and `wiki/pedagogy/a1/<slug>.md` plus sources files when present.

## Helpers And Headroom

Read-only helper explorers are allowed for module-shape summaries or consistency checks. Do not delegate final judgments. Use Headroom compression for helper summaries, logs, or search output over 200 lines or 20 KB. Do not use Headroom memory as curriculum authority.

## Durable Report Path

Write the report to `docs/audits/a1-quality-audit-YYYY-MM-DD.md`.

## Validation Commands

```bash
git status --short --branch
git diff --check
git diff --name-only
git diff --name-only | rg -v '^docs/audits/a1-quality-audit-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' || true
rg -n 'sys\.executable' docs/audits/a1-quality-audit-*.md
```

Do not run module builds. Do not run commands that write generated curriculum audit/status/review artifacts.

## Expected Final Response

```text
Report written: docs/audits/a1-quality-audit-YYYY-MM-DD.md
Scope inspected: <modules>
Blockers: <n>
Issues recorded: <n>
Recommended remediation batches: <summary>
Validation run: <commands and outcomes>
Curriculum files modified: no
swarm_used: true/false
swarm_note: <helpers used, or solo run; no swarm used>
```
