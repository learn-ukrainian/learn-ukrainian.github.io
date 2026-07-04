# B2 Quality Audit Orchestrator

Prompt version: 0.4
Last reviewed: 2026-06-22

## Source Assumptions

- This is a post-build audit for B2 modules, not a preflight plan audit.
- B2 should show higher abstraction, richer syntax, stylistic/register control, argumentation, and professional/academic readiness.
- This audit must not modify curriculum, wiki, discovery, or site sources. Its only content write is the durable report under `docs/audits/`, plus PR text needed to deliver that report.
- Do not assume every planned B2 module is built; audit only built modules in scope and record missing source directories separately.

## Goal

Review built B2 modules for B2-specific quality after production. Record a complete issue inventory without top-10 truncation, write a durable report, and propose remediation batches. Do not fix modules.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/b2-quality-audit .worktrees/dispatch/codex/b2-quality-audit origin/main
cd .worktrees/dispatch/codex/b2-quality-audit
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
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `curriculum/l2-uk-en/curriculum.yaml`, B2 section
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`
- `scripts/audit/config.py`
- target B2 production PR notes or build report if available
- for each built target slug:
  - `curriculum/l2-uk-en/plans/b2/<slug>.yaml`
  - `curriculum/l2-uk-en/b2/discovery/<slug>.yaml`
  - `curriculum/l2-uk-en/b2/<slug>/module.md`
  - `curriculum/l2-uk-en/b2/<slug>/activities.yaml`
  - `curriculum/l2-uk-en/b2/<slug>/vocabulary.yaml`
  - `curriculum/l2-uk-en/b2/<slug>/resources.yaml` if present
  - `wiki/grammar/b2/<slug>.md`
  - `wiki/grammar/b2/<slug>.sources.yaml`
  - `site/src/content/docs/b2/<slug>.mdx`

## Allowed Writes

- `docs/audits/b2-quality-audit-YYYY-MM-DD.md`
- PR body or final orchestration note text for delivering the report

## Forbidden Writes

- `curriculum/l2-uk-en/**`
- `wiki/**`
- `site/src/content/docs/**`
- `.python-version`, `.yamllint`, `.markdownlint.json`
- `data/telemetry/**`
- generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts

## Audit Checks

- Verify built-module scope against `curriculum.yaml`; record planned but unbuilt modules separately.
- Verify live B2 thresholds, immersion policy, activity types, and grammar constraints from code.
- Check plan fidelity: objectives, content outline, vocabulary hints, activity hints, phase goals, and references.
- Check source/wiki coverage and whether the module teaches from the local wiki rather than inventing source claims.
- Check B2 abstraction: advanced concepts are explained in Ukrainian without becoming opaque.
- Check richer syntax: multi-clause sentences are natural, controlled, and teachable; complexity is not decorative.
- Check register and style: formal/informal, business, academic, public discourse, literary, and cross-register tasks match the module goal.
- Check argumentation and professional/academic readiness: learners practice claims, evidence, counterargument, synthesis, reports, presentations, or analysis where appropriate.
- Check activities: they practice language skills, not trivia about the topic.
- Check vocabulary: enough B2 terms, register labels where useful, natural examples, and source-backed usage.
- Check engagement and wall-of-text risk: examples, tables, callouts, and tasks make dense material usable.
- Run deterministic module audits without `--fix` for built modules in scope where feasible, and record any failures alongside subjective findings.

## Helper Swarm Policy

Default to a solo audit for a narrow one-module report unless a helper will materially improve coverage or validation confidence. When helpers are useful, keep routine delegation to one to three helpers total.

- Use `gpt-5.4-mini` explorer helpers for read-only coverage matrices, source/wiki/plan comparisons, and validation summaries.
- Use `gpt-5.3-codex-spark` helpers only for narrow code-heavy validation such as parser, schema, or command-output triage.
- The main auditor owns final severity calls, issue inventory, remediation batching, PR creation, independent-family review routing, merge decisions, and git hygiene.
- Do not let helpers read secrets, source `.envrc`, call `gh`, request reviews, open PRs, merge PRs, or edit curriculum/site files.
- Record helper roles in the durable report and PR body; set `swarm_used: true` when any helper or reviewer thread did bounded audit work. Solo audits still require `swarm_used: false`, `swarm_label: none`, and `swarm_note`.
- For helper output or logs over 200 lines or 20 KB, summarize and push bulky evidence behind a file path or PR link.

## Durable Report Path

Write the report to `docs/audits/b2-quality-audit-YYYY-MM-DD.md`.

## Validation Commands

For multi-module audits, repeat the module audit and cleanup commands for every audited `<slug>`/`<module_num>` pair and record each command outcome in the durable report.

```bash
REPORT="docs/audits/b2-quality-audit-$(date +%F).md"
git status --short --branch
.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/<slug>/module.md
rm -f .cache/lemma-frequency-b2-<module_num>.json
rm -rf curriculum/l2-uk-en/b2/<slug>/audit curriculum/l2-uk-en/b2/<slug>/status
git diff --check
test -f "$REPORT"
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
printf '%s\n' "$CHANGED_FILES"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg -v '^docs/audits/b2-quality-audit-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$'; then
  echo "Unexpected file outside the durable audit report" >&2
  exit 1
fi
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
FORBIDDEN_INTERPRETER_TOKEN='sys[.]executable'
if rg -n "$FORBIDDEN_INTERPRETER_TOKEN" "$REPORT"; then
  echo "Audit report mentions forbidden interpreter token" >&2
  exit 1
fi
```

Adapt the `audit_module.py --skip-review` path and cleanup paths for each built module audited. Keep the review gate separate: cite the independent review source in the durable audit report or PR body. The audit command still writes local generated cache/status/audit outputs, so remove those known outputs before the diff gate; do not commit curriculum `review/`, `audit/`, or `status/` artifacts. Do not pass `--fix`. Do not run builds.

## Independent-Family Review Gate

Before merge, request a read-only independent-family review of the audit-report PR. Prefer Claude Opus 4.8. If Claude Opus 4.8 is unavailable, use Agy with Gemini 3.1 Pro High, for example `agy --model "Gemini 3.1 Pro (High)" --print-timeout 10m -p "<review prompt>"`.

The review prompt must include the PR diff, audited-module scope, validation summary, artifact-clean statement, helper/swarm note, and an explicit request for blocker-only findings. Record reviewer identity, review model, review scope, unresolved findings, and final disposition in the durable audit report or PR body. The merge rule is explicit: unresolved findings are blockers.

## PR Body Requirements

PR body must include: audited modules, report path, blocker count, issue count, recommended remediation batches, validation commands and outcomes, `swarm_used`, `swarm_label`, `swarm_note`, reviewer identity, review scope, final disposition, unresolved review findings count, and a statement that no curriculum/site source files, generated curriculum artifacts, or telemetry database files are included.

## Report Delivery

After validation, commit and open a draft PR that contains only the report plus PR body delivery text:

```bash
REPORT="docs/audits/b2-quality-audit-$(date +%F).md"
git add "$REPORT"
git commit -m "docs: add B2 quality audit" --trailer "X-Agent: codex/b2-quality-audit"
.venv/bin/python scripts/audit/lint_agent_trailer.py
git push -u origin codex/b2-quality-audit
gh pr create --draft --fill --head codex/b2-quality-audit --base main
```

## Expected Final Response

```text
Report written: docs/audits/b2-quality-audit-YYYY-MM-DD.md
Scope inspected: <modules>
Blockers: <n>
Issues recorded: <n>
Recommended remediation batches: <summary>
Validation run: <commands and outcomes>
Report delivery: <draft PR URL or blocked reason>
Review PR: <url, ready/merged/blocked>
Independent review: <reviewer identity, model, scope, final disposition>
Unresolved review findings: <n>
Curriculum files modified: no
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | solo | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
