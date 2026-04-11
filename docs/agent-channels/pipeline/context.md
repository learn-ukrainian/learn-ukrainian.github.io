# pipeline — v6 build, audit, dispatch

This channel is for conversations about the V6 module build pipeline
and its supporting infrastructure. If you're posting here, you're
discussing `scripts/build/v6_build.py`, `scripts/build/quick_verify.py`,
`scripts/audit/**`, `scripts/build/dispatch.py`, the agent_runtime
adapter, or anything else that touches how a module goes from plan →
prose → audit → review → publish.

## Reference architecture

V6 pipeline phases (see `scripts/build/phases/`):

```
check → research → skeleton → write → activities → enrich → verify → review → publish
```

- **check** — validates plan YAML, vocab, section structure
- **research** — builds knowledge packet from textbooks + wiki + RAG
- **skeleton** — paragraph-level scaffold (for ≥2000 word modules)
- **write** — prose generation (single-call or chunked if word_target ≥ 2000)
- **activities** — generates exercise blocks, fills INJECT_ACTIVITY markers
- **enrich** — tabs, vocabulary tables, stress marks, словник
- **verify** — quick_verify structural checks (char-budget, vocab coverage, toxic tokens)
- **review** — adversarial review by another agent with `<fixes>` output
- **publish** — MDX render to `starlight/`

## Key files

| File | What |
|---|---|
| `scripts/build/v6_build.py` | 6000-line god object — main pipeline orchestrator |
| `scripts/build/quick_verify.py` | Post-write structural checks |
| `scripts/build/phases/v6-write.md` | Write-phase prompt template |
| `scripts/build/dispatch.py` | Agent invocation (Gemini/Claude tools mode) |
| `scripts/audit/config.py` | Level-specific thresholds (word_target, engagement, priority_types) |
| `scripts/audit/checks/*.py` | Audit gate implementations |
| `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` | Module plan (immutable) |

## Non-negotiables

1. **Plans are the source of truth.** Never silently modify a plan — bump the version and backup the old one.
2. **Audit gates must ALL be green.** No "good enough" if one gate is failing.
3. **Word targets are minimums.** Expand content, never lower the target.
4. **Reviewer is not the writer.** Enforced by `SELF_REVIEW_DETECTED` audit gate.

## Common commands

```bash
.venv/bin/python scripts/build/v6_build.py a1 3               # build module 3 of A1
.venv/bin/python scripts/build/v6_build.py b1 N --slug X --step write --resume  # re-run write
.venv/bin/python -m pytest tests/test_quick_verify.py         # unit tests
```
