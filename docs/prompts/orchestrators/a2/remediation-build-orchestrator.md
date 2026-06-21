# A2 Remediation Build Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- This prompt consumes a durable A2 audit report under `docs/audits/`.
- A2 remediation must preserve transition-track pedagogy: easy Ukrainian first, concrete examples, controlled grammar, and a deliberate path toward B1.
- Do not flatten early A2 into full B1-style immersion. Do not retreat late A2 into A1-style English explanation unless current repo policy and the audit finding justify it.
- Plans are source of truth. Do not edit plans unless the user explicitly scopes a plan fix.

## Goal

Fix all findings from the selected A2 audit batch in small PR-sized batches. Regenerate generated site MDX for changed modules, validate the result, prepare PR-ready notes, and record module-build telemetry.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/a2-remediation-<batch> .worktrees/dispatch/codex/a2-remediation-<batch> origin/main
cd .worktrees/dispatch/codex/a2-remediation-<batch>
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
- the A2 audit report being remediated
- `curriculum/l2-uk-en/curriculum.yaml`
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`, especially A2 immersion policies
- `scripts/audit/config.py`
- for each target slug:
  - `curriculum/l2-uk-en/plans/a2/<slug>.yaml`
  - `curriculum/l2-uk-en/a2/<slug>/module.md`
  - `curriculum/l2-uk-en/a2/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/a2/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/a2/<slug>/resources.yaml` if present
  - `wiki/grammar/a2/<slug>.md`
  - `wiki/grammar/a2/<slug>.sources.yaml`
  - `site/src/content/docs/a2/<slug>.mdx`

## Allowed Writes

- For scoped target slugs only:
  - `curriculum/l2-uk-en/a2/<slug>/module.md`
  - `curriculum/l2-uk-en/a2/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/a2/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/a2/<slug>/resources.yaml`
  - `site/src/content/docs/a2/<slug>.mdx`
- PR body or final orchestration note text

## Forbidden Writes

- A2 plans unless explicitly authorized
- modules outside the selected audit batch
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Remediation Rules

- Fix every selected finding; do not truncate.
- Preserve phase-appropriate immersion from `scripts/config.py`.
- Use simple Ukrainian, repeated frames, concrete examples, dialogues, pattern boxes, and tables to solve clarity issues.
- Keep grammar within A2 limits: no participle-heavy enrichment, no literary register, no unscaffolded B1 syntax.
- Strengthen late-A2 B1 readiness through controlled Ukrainian metalanguage and short independent reading blocks.
- Keep activities as language practice using module content as context.
- Use the activity YAML shape already present in the module.
- Separate targeted patches from full rebuilds.

## Helpers And Headroom

Helpers are allowed for bounded validation, YAML checks, or source coverage checks with clear file ownership. The main orchestrator owns final pedagogy. Use Headroom compression for helper output or logs over 200 lines or 20 KB.

## Validation Commands

Adapt module numbers from `curriculum.yaml`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en a2 <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/a2/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en a2 <module_num> --validate
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a2/<slug>/module.md
git diff --check
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
```

Run `scripts/audit/check_mdx_generation_drift.py` only when a drift-only check is needed after generation.

## PR, Commit, And Telemetry Requirements

- Branch: `codex/a2-remediation-<batch>`
- Commit trailer: `X-Agent: codex/a2-remediation-<batch>`
- Run `.venv/bin/python scripts/audit/lint_agent_trailer.py` before pushing.
- Persist module-build telemetry using `docs/prompts/orchestrators/shared/telemetry-and-pr.md`.
- Include `swarm_used`, `swarm_label`, and `swarm_note` in telemetry and PR text.
- Require independent review before merge.

## Expected Final Response

```text
Audit report consumed: <path>
Batch fixed: <batch id>
Modules changed: <slugs>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted or unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | solo | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
