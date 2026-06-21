# A1 Remediation Build Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- This prompt consumes a durable A1 audit report under `docs/audits/`.
- A1 remediation fixes learner-facing module sources in small PR-sized batches.
- A1 is not a place for premature immersion. Preserve beginner tone, decodability, stress/pronunciation support, and scaffolded progression.
- Plans are source of truth. Do not edit plans unless the user explicitly scopes a plan fix.

## Goal

Fix all findings from the selected A1 audit batch without changing unrelated modules. Regenerate generated site MDX for changed modules, validate the result, prepare PR-ready notes, and record token telemetry for module-build work.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/a1-remediation-<batch> .worktrees/dispatch/codex/a1-remediation-<batch> origin/main
cd .worktrees/dispatch/codex/a1-remediation-<batch>
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
- the A1 audit report being remediated
- `curriculum/l2-uk-en/curriculum.yaml`
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`, especially A1 immersion policies
- `scripts/audit/config.py`
- for each target slug:
  - `curriculum/l2-uk-en/plans/a1/<slug>.yaml`
  - `curriculum/l2-uk-en/a1/<slug>/module.md`
  - `curriculum/l2-uk-en/a1/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/a1/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/a1/<slug>/resources.yaml` if present
  - `wiki/pedagogy/a1/<slug>.md`
  - `wiki/pedagogy/a1/<slug>.sources.yaml`
  - `site/src/content/docs/a1/<slug>.mdx`

## Allowed Writes

- For scoped target slugs only:
  - `curriculum/l2-uk-en/a1/<slug>/module.md`
  - `curriculum/l2-uk-en/a1/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/a1/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/a1/<slug>/resources.yaml`
  - `site/src/content/docs/a1/<slug>.mdx`
- PR body or final orchestration note text

## Forbidden Writes

- A1 plans unless explicitly authorized
- modules outside the selected audit batch
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Remediation Rules

- Fix every finding in the selected batch; do not pick only the top issues.
- Preserve A1 learner safety: short steps, supportive tone, and visible repair language.
- Preserve decodability: do not add unexplained Cyrillic clusters, long unglossed Ukrainian prose, or advanced grammar as "enrichment".
- Preserve current stress/pronunciation policy. Verify it locally before changing stress marks.
- Keep activities as language practice, not trivia. Use the existing V1 bare-list or V2 `inline:`/`workbook:` shape already present in the target file.
- Keep vocabulary useful, concrete, and level-appropriate; verify suspicious words against local tools before adding.
- Separate targeted patches from rebuilds. Rebuild only when the audit finding cannot be fixed safely with local edits.

## Helpers And Headroom

Helpers are allowed for bounded validation or mechanical YAML/MDX checks, with disjoint file ownership. Do not delegate final pedagogy decisions. Use Headroom compression for helper output or logs over 200 lines or 20 KB.

## Validation Commands

Adapt module numbers from `curriculum.yaml`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en a1 <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/a1/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en a1 <module_num> --validate
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/<slug>/module.md
git diff --check
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
```

Run additional targeted checks required by the audit report. Run `scripts/audit/check_mdx_generation_drift.py` only when a drift-only check is needed after generation. Do not include generated forbidden artifacts in the PR.

## PR, Commit, And Telemetry Requirements

- Branch: `codex/a1-remediation-<batch>`
- Commit trailer: `X-Agent: codex/a1-remediation-<batch>`
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
