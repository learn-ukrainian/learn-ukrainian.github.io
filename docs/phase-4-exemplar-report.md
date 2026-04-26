# Phase 4 Exemplar Report

## Scope

This pass establishes the Phase 4 linear pipeline foundation for A1/20
`my-morning` and creates draft module artifacts for the exemplar path.

## Completed

- Added `scripts/build/linear_pipeline.py` with plan validation, research
  packet wrapper, prompt rendering, writer invocation through
  `scripts.agent_runtime.runner.invoke`, deterministic Python QG, strict LLM
  QG dimension validation, review aggregation, and MDX assembly.
- Added Phase 4 prompt templates:
  - `scripts/build/phases/linear-write.md`
  - `scripts/build/phases/linear-review-dim.md`
- Added focused tests:
  - `tests/build/test_linear_pipeline.py`
  - `tests/build/test_a1_20_exemplar.py`
- Created draft A1/20 artifacts:
  - `curriculum/l2-uk-en/a1/my-morning/module.md`
  - `curriculum/l2-uk-en/a1/my-morning/activities.yaml`
  - `curriculum/l2-uk-en/a1/my-morning/vocabulary.yaml`
  - `curriculum/l2-uk-en/a1/my-morning/resources.yaml`
- Assembled draft MDX:
  - `starlight/src/content/docs/a1/my-morning.mdx`
- Wrote current Python QG output:
  - `audit/a1/my-morning.json`
- Wrote an explicit blocked LLM QG placeholder:
  - `review/a1/my-morning.json`

## Current Gate State

Python QG is red because `data/vesum.db` is absent in this worktree, so native
VESUM verification cannot run. With a fake verifier, the draft passes the
deterministic structural gates: word count, section headings and budgets,
immersion band, activity IDs, A1 activity type allowlist, AI-slop scan, citation
roundtrip, and the four separate cleanliness fields.

LLM QG is not complete. The pipeline validates the required exact five
dimensions before aggregation, but no live per-dimension reviewer calls were run
in this session.

MDX validation passes with:

```bash
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/build/mdx_validate.py starlight/src/content/docs/a1/my-morning.mdx
```

Starlight smoke build also passes after installing local dependencies:

```bash
cd starlight && npm ci && npm run build
```

## Pipeline Issues Surfaced

- The delegated worktree has no `.venv`, so commands using `.venv/bin/python`
  fail inside the worktree. I used the real local repo venv at
  `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- `data/vesum.db` is absent in the worktree, blocking real VESUM QG.
- The existing MDX generator turns HTML comments into `{/**/}`. The linear
  assembler strips empty JSX comments after generation so `mdx_validate.py`
  does not flag them as prose braces.
- The current generator renders activities in the workbook tab; inline
  `INJECT_ACTIVITY` replacement still needs Phase 5 integration work.

## Deferred

- Run the live Claude writer rather than using the hand-authored draft.
- Run five independent LLM QG reviewer calls and replace the blocked review
  placeholder with a real exact-`QG_DIMS` report.
- Run real VESUM verification after `data/vesum.db` is available.
- Replace the hand-authored draft with a live writer output once the writer
  call is available.
