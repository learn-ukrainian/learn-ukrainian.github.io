# B2 Production Build Orchestrator

Prompt version: 0.3
Last reviewed: 2026-06-22

## Source Assumptions

- Use this prompt only after `docs/audits/b2-preflight-readiness-*.md` says production may proceed.
- B2 modules require advanced Ukrainian immersion, register control, argumentation, professional/academic readiness, and richer syntax.
- B2 production should run in small sequential batches with module-tailored prompts, not generic batch instructions.
- Plans are source of truth. Do not edit plans unless a preflight remediation PR explicitly scopes that work.
- Some legacy B2 plans contain English planning scaffolding such as `Підсумок — Summary`, `Self-check`, English objectives, or English grammar labels. Treat that material as internal planning metadata only; do not copy it into B2 modules.
- Some B2 discovery YAML files are auto-generated keyword stubs with empty `rag_chunks` and `rag_literary`. Treat them as query-keyword scaffolding unless they contain source chunks.

## Goal

Build the selected B2 module batch from local plans, discovery files, and wiki/source coverage. Create source modules, activities, vocabulary, resources where needed, generate site MDX, validate, record telemetry, and require independent review before merge.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/b2-production-<batch> .worktrees/dispatch/codex/b2-production-<batch> origin/main
cd .worktrees/dispatch/codex/b2-production-<batch>
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
- passing or conditionally passing `docs/audits/b2-preflight-readiness-*.md`
- `curriculum/l2-uk-en/curriculum.yaml`, target B2 modules
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`, especially B2/default immersion policy
- `scripts/audit/config.py`, especially B2 thresholds and activity types
- for each target slug:
  - `curriculum/l2-uk-en/plans/b2/<slug>.yaml`
  - `curriculum/l2-uk-en/b2/discovery/<slug>.yaml`
  - `wiki/grammar/b2/<slug>.md`
  - `wiki/grammar/b2/<slug>.sources.yaml`
  - existing `curriculum/l2-uk-en/b2/<slug>/` source directory if present
  - existing `site/src/content/docs/b2/<slug>.mdx` if present

## Allowed Writes

- For scoped target slugs only:
  - `curriculum/l2-uk-en/b2/<slug>/module.md`
  - `curriculum/l2-uk-en/b2/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/b2/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/b2/<slug>/resources.yaml`
  - `site/src/content/docs/b2/<slug>.mdx`
  - `site/src/content/docs/b2/index.mdx` only if current repo generation or navigation requires it
- PR body or final orchestration note text

## Forbidden Writes

- B2 plans, discovery, or wiki files unless explicitly authorized by a preflight remediation scope
- modules outside the selected batch
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Production Rules

- Work in small sequential batches. Finish and validate each module before moving to the next.
- Write a module-tailored mini-prompt for each slug using that module's plan, discovery, wiki, and source YAML.
- In each module-tailored mini-prompt, include a `Plan Scaffolding Filter` note:
  - Ignore any plan section titled `Підсумок — Summary` or containing English `Self-check` prose as copy source.
  - Convert any legacy English planning notes into Ukrainian intent before writing.
  - Do not quote English plan prose in the module body.
  - English is allowed only in vocabulary translation/gloss contexts already permitted by live B2 config.
- In each module-tailored mini-prompt, include a `Discovery Authority Check` note:
  - If discovery YAML has empty `rag_chunks` and `rag_literary`, use only `query_keywords` as hints.
  - The authoritative teaching brief is `wiki/grammar/b2/<slug>.md` plus `<slug>.sources.yaml`.
  - Stop only when the target wiki article or source registry is missing, has no sources, or contains unresolved verification markers.
- B2 content should be advanced but teachable: richer syntax, register and style awareness, argumentation, professional or academic tasks, and precise vocabulary.
- Avoid generic filler, decorative complexity, and content trivia. Activities must practice Ukrainian language skills through the module topic.
- Maintain B2 immersion according to current config; English should be limited to vocabulary glosses or current repo-permitted contexts.
- If preflight blockers reappear, stop and record them rather than building around missing sources.

## Helpers And Headroom

Helpers are allowed for source extraction, validation, or independent review preparation. Assign clear file ownership for any worker. Use Headroom compression for helper output or logs over 200 lines or 20 KB.

## Validation Commands

Adapt module numbers from `curriculum.yaml`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en b2 <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en b2 <module_num> --validate
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2/<slug>/module.md
git diff --check
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
```

Run `scripts/audit/check_mdx_generation_drift.py` only when a drift-only check is needed after generation.

## PR, Commit, And Telemetry Requirements

- Branch: `codex/b2-production-<batch>`
- Commit trailer: `X-Agent: codex/b2-production-<batch>`
- Run `.venv/bin/python scripts/audit/lint_agent_trailer.py` before pushing.
- Persist module-build telemetry using `docs/prompts/orchestrators/shared/telemetry-and-pr.md`.
- Include `swarm_used`, `swarm_label`, and `swarm_note` in telemetry and PR text.
- Require independent review before merge.

## Expected Final Response

```text
B2 preflight report used: <path>
Modules built: <slugs>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted or unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | solo | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
