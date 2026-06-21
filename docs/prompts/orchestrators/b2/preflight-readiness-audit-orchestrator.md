# B2 Preflight Readiness Audit Orchestrator

Prompt version: 0.2
Last reviewed: 2026-06-21

## Source Assumptions

- B2 is the upcoming production track. Do not build modules until readiness passes.
- Current local repo contains B2 plans, discovery YAML, and wiki grammar/source files; built `curriculum/l2-uk-en/b2/<slug>/module.md` directories may not exist.
- Check Ukrainian State Standard 2024 alignment only through repo-supported sources, plan references, source YAML, and local docs. Do not invent external standards or unsupported claims.
- This audit must not modify plans, wiki, curriculum, discovery, or site sources. Its only content write is the durable report under `docs/audits/`, plus PR text needed to deliver that report.

## Goal

Determine whether B2 is ready for module production. Validate plans, sequence, `curriculum.yaml` alignment, wiki/grammar articles, source YAML coverage, research/source coverage, stale slugs, sequencing, and standard-alignment blockers. Output a readiness report with explicit "do not build until fixed" blockers. Do not fix plans or build modules.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/b2-preflight-readiness .worktrees/dispatch/codex/b2-preflight-readiness origin/main
cd .worktrees/dispatch/codex/b2-preflight-readiness
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
- `curriculum/l2-uk-en/curriculum.yaml`, B2 section
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`
- `scripts/audit/config.py`
- all B2 plans under `curriculum/l2-uk-en/plans/b2/`
- all B2 discovery files under `curriculum/l2-uk-en/b2/discovery/`
- all B2 wiki and source files under `wiki/grammar/b2/`
- relevant local docs or plan references that mention Ukrainian State Standard 2024

## Allowed Writes

- `docs/audits/b2-preflight-readiness-YYYY-MM-DD.md`
- PR body or final orchestration note text for delivering the report

## Forbidden Writes

- `curriculum/l2-uk-en/**`
- `wiki/**`
- `site/src/content/docs/**`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Readiness Checks

- Confirm every B2 slug in `curriculum.yaml` has exactly one plan file.
- Confirm every plan slug and sequence matches the manifest.
- Confirm discovery YAML coverage for every planned B2 slug.
- Confirm `wiki/grammar/b2/<slug>.md` and `<slug>.sources.yaml` coverage for every planned B2 slug.
- Identify stale plan files, `.bak` files, orphan wiki files, missing discovery files, missing source YAML, and naming mismatches.
- Check plan quality: objectives, content outline, vocabulary hints, activity hints, references, phase labels, and B2-appropriate register.
- Check sequencing: prerequisites appear before dependent modules; checkpoints and domain vocabulary are positioned coherently.
- Check source coverage against repo-supported Ukrainian State Standard 2024 references. If support is absent, record a source gap instead of inventing alignment.
- Identify blockers that require plan/wiki/source work before production.
- Mark readiness as `pass`, `conditional pass`, or `do not build`.

## Helpers And Headroom

Read-only helpers are allowed for inventories or slug-matrix checks. The main auditor owns readiness judgment. Use Headroom compression for helper output or search results over 200 lines or 20 KB.

## Durable Report Path

Write the report to `docs/audits/b2-preflight-readiness-YYYY-MM-DD.md`.

## Validation Commands

```bash
REPORT="docs/audits/b2-preflight-readiness-$(date +%F).md"
.venv/bin/python scripts/validate_plans.py b2
git status --short --branch
git diff --check
test -f "$REPORT"
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
printf '%s\n' "$CHANGED_FILES"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg -v '^docs/audits/b2-preflight-readiness-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$'; then
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

Do not run builds. Do not modify B2 plans, wiki files, discovery files, or modules.

## Report Delivery

After validation, commit and open a draft PR that contains only the report:

```bash
REPORT="docs/audits/b2-preflight-readiness-$(date +%F).md"
git add "$REPORT"
git commit -m "docs: add B2 preflight readiness audit" --trailer "X-Agent: codex/b2-preflight-readiness"
.venv/bin/python scripts/audit/lint_agent_trailer.py
git push -u origin codex/b2-preflight-readiness
gh pr create --draft --fill --head codex/b2-preflight-readiness --base main
```

## Expected Final Response

```text
Report written: docs/audits/b2-preflight-readiness-YYYY-MM-DD.md
Readiness status: pass | conditional pass | do not build
Blockers: <n>
Source/wiki/plan gaps: <summary>
Validation run: <commands and outcomes>
Report delivery: <draft PR URL or blocked reason>
B2 production allowed now: yes/no
Curriculum files modified: no
swarm_used: true/false
swarm_label: <none | solo | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
