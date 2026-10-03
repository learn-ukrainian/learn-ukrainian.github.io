# AGY sealed formal CF isolation (#5555)

## Status (2026-07-23 — v1 residual Option C)

Design spikes closed **Option C fail-closed residual** (not permanent wontfix for
future isolation engineering). For **fleet-comms v1 (#5512)**, AGY remains a live
**orchestrator** seat and is **not** a sealed formal CF reviewer.

| Capability | AGY (Antigravity / Gemini) | Formal CF sealed path |
| --- | --- | --- |
| Project instructions suppress | **Unproven** for sealed review | Fail-closed |
| Ambient MCP / hooks / nested reviewers | **Unproven** | Fail-closed |
| Sealed snapshot cwd only | Hard raise in `prepare_isolated_review_launch` | Refuse |
| `review-pr --reviewer agy` | Retired (#8520) | Replaced by direct `ask-* --type review` substitute seats |
| Registry `formal_review_eligible` | `false` for `agy` | **v1 complete residual** |
| Wire #5615 / enable #5616 | Residual closeout | Reopen only with Option A/B proof |

**Proof command (must stay green):**

```bash
.venv/bin/python -m pytest tests/test_review_isolation.py -k agy_isolated -q
# expect: ReviewIsolationError agy_isolated_review_unsupported
```

## Catalog seat vs formal reviewer (do not conflate)

AGY is a catalog seat (`orchestrator_seats.agy`) for bounded work and Ukrainian content review. It is **not** a planning, design or driver seat (operator decision 2026-10-03, #9584):

| Role | Model | Status |
| --- | --- | --- |
| Bounded worker / content review | `gemini-3.8-flash-high` @ high | **Live** (`orchestrator_seats.agy`); never a driver |
| Deep escalate | `gemini-3.8-flash-high` @ high | Same SKU escalation (`orchestrator_seats.agy`) |
| Sealed formal CF *reviewer* | — | **Blocked** until isolation proof (#5555) |

Formal CF for AGY-authored work is requested by the driver of record via direct `ask-<lane> --type review`
(codex|claude|glm|grok; sealed `review-pr` removed in #8520). Nobody may treat `ask-agy --review` as sealed formal CF.

## Live lane (non-formal / bounded work)

```bash
.venv/bin/python scripts/delegate.py dispatch --agent agy --model gemini-3.8-flash-high \
  --mode danger --worktree --task-id <task> --prompt-file BRIEF
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy - \
  --task-id agy-bounded --to-model gemini-3.8-flash-high
```

## Substitute formal CF

```bash
# Direct ask-* cross-family review (replaces removed review-pr):
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude - --type review --pr <N> --task-id review-<N> < prompt.md
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex - --type review --pr <N> --task-id review-<N> < prompt.md
```

## Flip criteria (do not skip)

1. Isolation matrix: project-instruction / MCP / hooks / nested-reviewer suppression proven.
2. `prepare_isolated_review_launch(engine="agy")` positive + negative tests.
3. Sealed transport registration (`ask-agy --type review` or equivalent) with receipts.
4. Smoke formal CF on a non-Google-family-authored PR.
5. Flip `formal_review_eligible: true` via CF'd enablement PR.

Parent: #5555 · stream #4707 · product #5512.
