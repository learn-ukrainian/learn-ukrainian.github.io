# B1 Remediation Build Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- This prompt consumes a durable B1 normalization audit report under `docs/audits/`.
- B1 remediation fixes M1-M82 issues in PR-sized batches.
- M93-M94 finale work is out of scope unless the user explicitly selects a finale batch.
- B1 module body should remain full Ukrainian immersion according to current repo policy.

## Goal

Fix all findings from the selected B1 normalization batch. Separate targeted patches from full rebuilds, keep changes scoped to selected modules, regenerate MDX, validate, prepare PR-ready notes, and record module-build telemetry.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/b1-remediation-<batch> .worktrees/dispatch/codex/b1-remediation-<batch> origin/main
cd .worktrees/dispatch/codex/b1-remediation-<batch>
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
- the B1 audit report being remediated
- `curriculum/l2-uk-en/curriculum.yaml`
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`, especially B1 immersion policy
- `scripts/audit/config.py`
- for each target slug:
  - `curriculum/l2-uk-en/plans/b1/<slug>.yaml`
  - `curriculum/l2-uk-en/b1/<slug>/module.md`
  - `curriculum/l2-uk-en/b1/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/b1/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/b1/<slug>/resources.yaml` if present
  - `wiki/grammar/b1/<slug>.md`
  - `wiki/grammar/b1/<slug>.sources.yaml`
  - `site/src/content/docs/b1/<slug>.mdx`

## Allowed Writes

- For scoped target slugs only:
  - `curriculum/l2-uk-en/b1/<slug>/module.md`
  - `curriculum/l2-uk-en/b1/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/b1/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/b1/<slug>/resources.yaml`
  - `site/src/content/docs/b1/<slug>.mdx`
- PR body or final orchestration note text

## Forbidden Writes

- B1 plans unless explicitly authorized
- M93-M94 or other finale files unless explicitly in scope
- modules outside the selected batch
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Remediation Rules

- Fix every selected finding; no top-10 truncation.
- Keep M1-M82 normalization separate from finale building.
- Prefer targeted patches for localized issues: missing examples, weak activity item, vocabulary gap, stress policy mismatch, or source citation repair.
- Use full rebuilds only when the module structure is fundamentally below bar or the audit report recommends a rebuild.
- Preserve B1 Ukrainian-only body text and grammar metalanguage.
- Do not contaminate older modules with M93-M94 finale synthesis unless the audit explicitly requests a local cross-reference.
- Keep activities as language practice and preserve the YAML shape already present.

## Helpers And Headroom

Helpers are allowed for mechanical validation or bounded source checks with clear file ownership. The main orchestrator owns integration and final pedagogy. Use Headroom compression for helper output or logs over 200 lines or 20 KB.

## Validation Commands

Adapt module numbers from `curriculum.yaml`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en b1 <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b1/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en b1 <module_num> --validate
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/<slug>/module.md
git diff --check
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
```

Run `scripts/audit/check_mdx_generation_drift.py` only when a drift-only check is needed after generation.

## PR, Commit, And Telemetry Requirements

- Branch: `codex/b1-remediation-<batch>`
- Commit trailer: `X-Agent: codex/b1-remediation-<batch>`
- Run `.venv/bin/python scripts/audit/lint_agent_trailer.py` before pushing.
- Persist module-build telemetry using `docs/prompts/orchestrators/shared/telemetry-and-pr.md`.
- Include `swarm_used`, `swarm_label`, and `swarm_note` in telemetry and PR text.
- Require independent review before merge.

## Expected Final Response

```text
Audit report consumed: <path>
Batch fixed: <batch id>
Modules changed: <slugs>
Targeted patches: <n>
Full rebuilds: <n>
Validation run: <commands and outcomes>
Telemetry: <posted or unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | solo | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
