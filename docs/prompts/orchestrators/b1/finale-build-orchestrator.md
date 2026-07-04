# B1 Finale Build Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- This prompt is for final B1 synthesis, checkpoint, review, or exam modules such as M93 `comprehensive-b1-review` and M94 `practice-exam`.
- Recent main has built source directories for M93-M94. Verify current checkout state before writing, and treat existing finale modules as remediation or hardening work rather than fresh creation.
- Finale work is separate from M1-M82 normalization.
- Earlier B1 modules are context and prerequisites unless explicitly unlocked for fixes.

## Goal

Build, finish, or remediate final B1 synthesis/checkpoint/exam modules in a small sequential batch. Respect locked/unlocked module rules, update generated site MDX and indexes only where current repo workflows require it, validate, record telemetry, and require independent review before merge.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/b1-finale-<batch> .worktrees/dispatch/codex/b1-finale-<batch> origin/main
cd .worktrees/dispatch/codex/b1-finale-<batch>
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
- `curriculum/l2-uk-en/curriculum.yaml`, B1 M83-M94
- `scripts/config.py`, `scripts/audit/config.py`
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- target finale plans:
  - `curriculum/l2-uk-en/plans/b1/comprehensive-b1-review.yaml`
  - `curriculum/l2-uk-en/plans/b1/practice-exam.yaml`
- target finale wiki:
  - `wiki/grammar/b1/comprehensive-b1-review.md`
  - `wiki/grammar/b1/practice-exam.md`
- recent B1 quality bar modules M83-M92 where present, especially `reported-speech`, `checkpoint-syntax`, `text-register-formal`, `checkpoint-text-register`, `narrative-mastery`, and `debate-and-opinion`
- current generated site structure under `site/src/content/docs/b1/`, including `index.mdx` if present

## Allowed Writes

- For explicitly selected finale slugs only:
  - `curriculum/l2-uk-en/b1/<slug>/module.md`
  - `curriculum/l2-uk-en/b1/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/b1/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/b1/<slug>/resources.yaml`
  - `site/src/content/docs/b1/<slug>.mdx`
  - `site/src/content/docs/b1/index.mdx` only if current repo generation or navigation requires it
- PR body or final orchestration note text

## Forbidden Writes

- M1-M82 normalization files unless explicitly authorized
- plans unless explicitly authorized
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Locked And Unlocked Rules

- Treat M1-M92 as locked context by default. Read them for prerequisite coverage, but do not edit them.
- The selected finale modules are unlocked for creation or remediation.
- If a finale build reveals an upstream blocker in M1-M92, document it and stop or ask for scope expansion; do not silently edit upstream modules.
- Finale modules should synthesize B1 skills rather than introduce new grammar.
- Checkpoint/exam activities should diagnose and practice Ukrainian language skills, not test trivia.

## Helpers

Helpers are allowed for prerequisite inventory, validation, or independent pre-review. The main orchestrator owns final build decisions. For helper output or logs over 200 lines or 20 KB, summarize and push bulky evidence behind a file path or PR link.

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

- Branch: `codex/b1-finale-<batch>`
- Commit trailer: `X-Agent: codex/b1-finale-<batch>`
- Run `.venv/bin/python scripts/audit/lint_agent_trailer.py` before pushing.
- Persist module-build telemetry using `docs/prompts/orchestrators/shared/telemetry-and-pr.md`.
- Include `swarm_used`, `swarm_label`, and `swarm_note` in telemetry and PR text.
- Require independent review before merge.

## Expected Final Response

```text
Finale modules built: <slugs>
Locked modules edited: none, or explicit list with authorization
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted or unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | solo | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
