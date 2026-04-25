# Unit 6 Phase A - Baseline (Claude writer / Codex reviewer)

- Outcome: FAIL
- module_done emitted: no
- MIN dim score: N/A (audit did not run)
- Convergence rounds used: 0
- Audit gates: failed: build stopped before audit
- Build wall clock: <1m

## Per-dim scores

| Dim | Score | Verdict           |
| --- | ---   | ---               |
| N/A | N/A   | Audit did not run |

## Notable findings

The forced build was invoked with:

```text
.venv/bin/python -u scripts/build/v6_build.py a1 1 --force --writer claude-tools --reviewer codex-tools
```

It passed the plan check and generated the research packet, then stopped during
Step 4 (`SKELETON`) before prose, activities, vocabulary, audit, or review were
produced.

Terminal failure:

```text
RuntimeError: Claude CLI < 2.1.116 inherits known quality regressions fixed on 2026-04-23 (see https://www.anthropic.com/engineering/april-23-postmortem). Upgrade with: npm install -g @anthropic-ai/claude-cli@latest
```

Preflight verification passed before the build:

- `scripts/api/logging.json` uses `uvicorn.logging.AccessFormatter`.
- `letter_module: true` is present for a1/1.
- 33 alphabet letter entries are present in `vocabulary_hints.recommended`.
- All five v6 write prompt blocks are present.
- A1 `min_types_unique` is `4`.

## Prose excerpt (first dialogue + first letter activity)

Not available. The build stopped before lesson prose was produced.
