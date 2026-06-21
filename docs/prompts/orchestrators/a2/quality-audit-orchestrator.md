# A2 Quality Audit Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- A2 is a transition track, not A1 with more words and not early B1.
- Current repo policy gives A2 a steep Ukrainian immersion ramp. Verify exact bands from `scripts/config.py` before judging.
- A2 must prepare learners for B1 grammar-in-Ukrainian while preserving controlled register, concrete examples, and support.
- This audit must not modify curriculum or site sources. Its only content write is the durable report under `docs/audits/`, plus PR text needed to deliver that report.

## Goal

Audit A2 modules for transition-track pedagogy: immersion ramp, grammar complexity, B1 readiness, wall-of-text risk, engagement, activity variety, vocabulary completeness, stress/pronunciation policy, and source/wiki coverage. Record every issue and propose remediation batches. Do not fix modules.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/a2-quality-audit .worktrees/dispatch/codex/a2-quality-audit origin/main
cd .worktrees/dispatch/codex/a2-quality-audit
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
- `curriculum/l2-uk-en/curriculum.yaml`, A2 section
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `docs/runbooks/module-build-token-telemetry.md`
- `scripts/config.py`
- `scripts/audit/config.py`
- representative A2 files before expanding scope:
  - `curriculum/l2-uk-en/a2/a2-bridge/module.md`
  - `curriculum/l2-uk-en/a2/aspect-concept/module.md`
  - `curriculum/l2-uk-en/a2/aspect-in-vocabulary/module.md`
  - `curriculum/l2-uk-en/a2/locative-expanded/module.md`
  - `curriculum/l2-uk-en/a2/a2-finale/module.md`
  - matching activities, vocabulary, resources, plans, `wiki/grammar/a2/`, and `site/src/content/docs/a2/`

## Allowed Writes

- `docs/audits/a2-quality-audit-YYYY-MM-DD.md`
- PR body or final orchestration note text for delivering the report

## Forbidden Writes

- `curriculum/l2-uk-en/**`
- `site/src/content/docs/**`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Audit Checks

- Verify A2 sequence and module numbers from `curriculum.yaml`.
- Verify live A2 thresholds, immersion policies, grammar constraints, activity types, and stress/pronunciation policy from code before judging.
- Check the immersion ramp by phase: early A2 should be easy Ukrainian with controlled scaffolding; late A2 should prepare for B1 without becoming dense B1 prose.
- Check grammar complexity: all cases are in play, aspect pairs are introduced, simple subordinate clauses appear, participles stay out unless current policy allows fixed forms.
- Check wall-of-text risk: long Ukrainian explanations need tables, pattern boxes, dialogues, examples, and review loops.
- Check B1 readiness: late A2 should increase Ukrainian metalanguage, independent reading practice, and controlled multi-clause sentences.
- Check engagement and examples: concrete everyday situations, not abstract grammar walls.
- Check activities: variety, item quality, inline/workbook split where present, and language-practice focus.
- Check vocabulary: terms are useful, examples are natural, and coverage matches the plan.
- Check source/wiki coverage: each module should align with `curriculum/l2-uk-en/plans/a2/<slug>.yaml` and `wiki/grammar/a2/<slug>.md` plus sources.
- Run deterministic module audits without `--fix` for built modules in scope where feasible, and record any failures alongside subjective findings.

## Helpers And Headroom

Read-only explorers are allowed for phase summaries, module-shape surveys, or consistency checks. The main auditor owns final issue severity. Use Headroom compression for helper output or long search results over 200 lines or 20 KB.

## Durable Report Path

Write the report to `docs/audits/a2-quality-audit-YYYY-MM-DD.md`.

## Validation Commands

```bash
REPORT="docs/audits/a2-quality-audit-$(date +%F).md"
git status --short --branch
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a2/<slug>/module.md
git diff --check
test -f "$REPORT"
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
printf '%s\n' "$CHANGED_FILES"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg -v '^docs/audits/a2-quality-audit-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$'; then
  echo "Unexpected file outside the durable audit report" >&2
  exit 1
fi
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
if rg -n 'sys\.executable' "$REPORT"; then
  echo "Audit report mentions forbidden sys.executable" >&2
  exit 1
fi
```

Adapt the `audit_module.py` path for each built module audited. Do not pass `--fix`. Do not run module builds. Do not run commands that write generated curriculum audit/status/review artifacts.

## Report Delivery

After validation, commit and open a draft PR that contains only the report:

```bash
REPORT="docs/audits/a2-quality-audit-$(date +%F).md"
git add "$REPORT"
git commit -m "docs: add A2 quality audit" --trailer "X-Agent: codex/a2-quality-audit"
.venv/bin/python scripts/audit/lint_agent_trailer.py
git push -u origin codex/a2-quality-audit
gh pr create --draft --fill --head codex/a2-quality-audit --base main
```

## Expected Final Response

```text
Report written: docs/audits/a2-quality-audit-YYYY-MM-DD.md
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
