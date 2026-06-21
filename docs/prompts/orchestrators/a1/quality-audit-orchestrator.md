# A1 Quality Audit Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- A1 is the beginner track. Do not judge it by B1 or B2 immersion habits.
- Current repo examples show A1 uses English support, short Ukrainian chunks, stress marks, letter/sound work, and warm repair language.
- Thresholds and stress/pronunciation rules must be verified from `scripts/config.py`, `scripts/audit/config.py`, and current docs before judging.
- This audit must not modify curriculum or site sources. Its only content write is the durable report under `docs/audits/`, plus PR text needed to deliver that report.

## Goal

Audit A1 modules for beginner-safe pedagogy, emotional safety, scaffolding, Cyrillic/decodability, pronunciation support, activity quality, vocabulary usefulness, and source/wiki coverage. Record every issue found and propose remediation batches. Do not fix modules.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/a1-quality-audit .worktrees/dispatch/codex/a1-quality-audit origin/main
cd .worktrees/dispatch/codex/a1-quality-audit
test -e .venv || ln -s "$REPO_ROOT/.venv" .venv
export WORKTREE_ROOT="$(pwd)"
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
- PR body or final orchestration note text for delivering the report

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
- Run deterministic module audits without `--fix` for built modules in scope where feasible, and record any failures alongside subjective findings.

## Helpers And Headroom

Read-only helper explorers are allowed for module-shape summaries or consistency checks. Do not delegate final judgments. Use Headroom compression for helper summaries, logs, or search output over 200 lines or 20 KB. Do not use Headroom memory as curriculum authority.

## Durable Report Path

Write the report to `docs/audits/a1-quality-audit-YYYY-MM-DD.md`.

## Report Delivery

After validation, commit and open a draft PR that contains only the report:

```bash
git add docs/audits/a1-quality-audit-YYYY-MM-DD.md
git commit -m "docs: add A1 quality audit" --trailer "X-Agent: codex/a1-quality-audit"
.venv/bin/python scripts/audit/lint_agent_trailer.py
git push -u origin codex/a1-quality-audit
gh pr create --draft --fill --head codex/a1-quality-audit --base main
```

## Validation Commands

```bash
git status --short --branch
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/<slug>/module.md
git diff --check
git diff --name-only
if git diff --name-only | rg -v '^docs/audits/a1-quality-audit-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$'; then
  echo "Unexpected file outside the durable audit report" >&2
  exit 1
fi
if git diff --name-only | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
if rg -n 'sys\.executable' docs/audits/a1-quality-audit-YYYY-MM-DD.md; then
  echo "Audit report mentions forbidden sys.executable" >&2
  exit 1
fi
```

Adapt the `audit_module.py` path for each built module audited. Do not pass `--fix`. Do not run module builds. Do not run commands that write generated curriculum audit/status/review artifacts.

## Expected Final Response

```text
Report written: docs/audits/a1-quality-audit-YYYY-MM-DD.md
Scope inspected: <modules>
Blockers: <n>
Issues recorded: <n>
Recommended remediation batches: <summary>
Validation run: <commands and outcomes>
Report delivery: <draft PR URL or blocked reason>
Curriculum files modified: no
swarm_used: true/false
swarm_note: <helpers used, or solo run; no swarm used>
```
