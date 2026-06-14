# Dispatch brief — B1 M13 alternation-consonants-verbs

Use this prompt for a fresh high-reasoning implementation thread.

## Thread setup

Model: GPT-5.5, xhigh reasoning.

Role: B1 module builder and local orchestrator. Use a small bounded swarm, but keep the main thread responsible for integration, final diff review, validation, commit, PR, and merge-readiness.

Repo: `/Users/krisztiankoos/projects/learn-ukrainian`

Worktree:

```bash
git worktree add -b codex/b1-m13-alternation-verbs .worktrees/dispatch/codex/b1-m13-alternation-verbs origin/main
cd .worktrees/dispatch/codex/b1-m13-alternation-verbs
test -e .venv || ln -s /Users/krisztiankoos/projects/learn-ukrainian/.venv .venv  # venv symlinked
```

If that branch or path already exists, inspect it first and do not overwrite user work.

## Required first reads

- `AGENTS.md`
- `docs/decisions/2026-06-14-a1-a2-live-maintenance-and-workbook-enrichment.md`
- `curriculum/l2-uk-en/curriculum.yaml` B1 section
- `curriculum/l2-uk-en/plans/b1/alternation-consonants-verbs.yaml`
- The built B1.1 predecessors:
  - `curriculum/l2-uk-en/b1/alternation-vowels/module.md`
  - `curriculum/l2-uk-en/b1/alternation-vowels/activities.yaml`
  - `curriculum/l2-uk-en/b1/alternation-consonants-nouns/module.md`
  - `curriculum/l2-uk-en/b1/alternation-consonants-nouns/activities.yaml`

## Objective

Build B1 M13 only:

- slug: `alternation-consonants-verbs`
- level sequence: B1 module 13
- title: `Чергування приголосних (дієслова)`
- source plan: `curriculum/l2-uk-en/plans/b1/alternation-consonants-verbs.yaml`

Expected output scope:

- `curriculum/l2-uk-en/b1/alternation-consonants-verbs/module.md`
- `curriculum/l2-uk-en/b1/alternation-consonants-verbs/activities.yaml`
- `curriculum/l2-uk-en/b1/alternation-consonants-verbs/vocabulary.yaml`
- `curriculum/l2-uk-en/b1/alternation-consonants-verbs/resources.yaml`
- `site/src/content/docs/b1/alternation-consonants-verbs.mdx`
- `site/src/content/docs/b1/index.mdx` only if the landing/index must be regenerated to expose M13

Do not touch unrelated modules. Do not include generated `status/*.json`, `audit/*-review.md`, `review/*-review.md`, docs session-state files, or linter/python-version config.

## Content contract

- Match the M01-M12 B1 style now on `main`: natural B1 Ukrainian, no stress marks, no filler, no Russianisms.
- Activity YAML must be V2: top-level `inline:` and `workbook:`, never an `activities:` wrapper.
- Target activity count: 5 inline + 11 workbook, 16 total.
- Workbook IDs: `wb-1` through `wb-11`.
- Keep examples accurate:
  - dental/sibilant alternations: `водити — воджу`, `крутити — кручу`, `возити — вожу`, `носити — ношу`
  - complex clusters: `їздити — їжджу`, `простити — прощу`, `чистити — чищу`
  - velars: `могти — можу`, `пекти — печу`, `махати — машу`
  - labial + `л`: `робити — роблю`, `купити — куплю`, `ловити — ловлю`
- Make the limiting rule explicit: alternation appears in the first-person singular form, not throughout the paradigm.
- Avoid overclaiming imperative behavior; verify examples before using them.
- Include exercises that force learners to distinguish alternation from unchanged forms in other persons.

## Swarm plan

Use at most three bounded helpers:

1. Source/schema scout, read-only:
   - Verify M13 plan constraints and compare M11-M12 predecessor style.
   - Report required activity types, vocabulary expectations, and schema pitfalls.
2. Linguistic/pedagogical reviewer, read-only:
   - Review the drafted M13 module and activities for Ukrainian correctness, B1 appropriateness, and Russianism/calque risk.
3. Validation runner, read-only:
   - Run deterministic checks only: YAML parse/schema, activity validation, MDX render/validate, `git diff --check`, and targeted site build if needed.

The main thread owns all edits. Helpers must not touch files unless explicitly re-dispatched with a tight file boundary.

## Validation

Run the narrowest local gates available for changed artifacts. Prefer existing project scripts over ad hoc checks. Minimum:

```bash
git diff --check
test -e .venv || ln -s /Users/krisztiankoos/projects/learn-ukrainian/.venv .venv  # venv symlinked
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in [
    "curriculum/l2-uk-en/b1/alternation-consonants-verbs/activities.yaml",
    "curriculum/l2-uk-en/b1/alternation-consonants-verbs/vocabulary.yaml",
    "curriculum/l2-uk-en/b1/alternation-consonants-verbs/resources.yaml",
]:
    yaml.safe_load(Path(path).read_text(encoding="utf-8"))
print("yaml ok")
PY
```

Also run the project’s activity/schema and MDX/site validation commands that match the current scripts discovered in the worktree. Do not weaken tests or linter configs.

## Commit and PR

Commit only the M13 files and any required B1 index/landing update.

Commit message:

```text
content(b1): build M13 alternation consonants in verbs

X-Agent: codex/b1-m13-alternation-verbs
```

Open a draft PR after local validation. The PR body must include:

- changed files
- validation commands with raw final output
- note that generated audit/status/review artifacts are excluded
- independent review status and any remaining risks

Do not merge until CI is green and independent review has no blockers.
