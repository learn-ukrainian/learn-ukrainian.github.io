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
| `review-pr --reviewer agy` | **Not implemented** | Use substitute seats |
| Registry `formal_review_eligible` | `false` for `agy` | **v1 complete residual** |
| Wire #5615 / enable #5616 | Residual closeout | Reopen only with Option A/B proof |

**Proof command (must stay green):**

```bash
.venv/bin/python -m pytest tests/test_review_isolation.py -k agy_isolated -q
# expect: ReviewIsolationError agy_isolated_review_unsupported
```

## Orchestrator vs formal reviewer (do not conflate)

AGY **is** an orchestrator seat for fleet-comms (#5512):

| Role | Model | Status |
| --- | --- | --- |
| Orchestrator loop | `gemini-3.6-flash-high` @ high | **Live** (`orchestrator_seats.agy`) |
| Deep escalate | `gemini-3.1-pro-high` @ high | Optional, not default loop |
| Sealed formal CF *reviewer* | — | **Blocked** until isolation proof (#5555) |

When AGY orchestrates, it **requests** CF via `review-pr` (codex|claude|glm). It must not treat `ask-agy --review` as sealed formal CF.

## Live lane (non-formal / orchestrator)

```bash
.venv/bin/python scripts/delegate.py dispatch --agent agy --model gemini-3.6-flash-high \
  --mode danger --worktree --task-id <task> --prompt-file BRIEF
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy - \
  --task-id agy-orch --to-model gemini-3.6-flash-high
```

## Substitute formal CF

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N>
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> --reviewer claude
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> --reviewer glm
```

## Flip criteria (do not skip)

1. Isolation matrix: project-instruction / MCP / hooks / nested-reviewer suppression proven.
2. `prepare_isolated_review_launch(engine="agy")` positive + negative tests.
3. Sealed transport registration (`review-pr --reviewer agy` or equivalent) with receipts.
4. Smoke formal CF on a non-Google-family-authored PR.
5. Flip `formal_review_eligible: true` via CF'd enablement PR.

Parent: #5555 · stream #4707 · product #5512.
