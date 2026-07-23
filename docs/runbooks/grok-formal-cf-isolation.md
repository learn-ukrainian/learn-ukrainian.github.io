# Grok sealed formal CF isolation (#5557)

## Status (2026-07-23 — v1 residual Option C)

Design spikes closed **Option C fail-closed residual**. For **fleet-comms v1 (#5512)**,
Grok is a live **orchestrator / implement** seat and is **not** a sealed formal CF reviewer.

| Capability | Native Grok CLI | Formal CF sealed path |
| --- | --- | --- |
| OAuth / session auth staged without tool-visible credentials | **Fails** — native OAuth store cannot be hidden from required Read/Grep/Glob tools while still authenticating | Fail-closed |
| Auth never staged into model-read scope | **Proven** (tests: `test_grok_oauth_store_is_never_staged_*`) | Correct refusal, not a silent leak |
| Sealed snapshot cwd + OS sandbox | Not reached for `engine=grok` | Hard raise before launch |
| `review-pr --reviewer grok` | **Not implemented** (reviewers: `auto\|codex\|glm\|claude` only) | Use substitute seats |
| Registry `formal_review_eligible` | `false` for `grok` | **v1 complete residual** |
| Wire #5621 / enable #5622 | Residual closeout | Reopen only with Option A/B proof |
| Cursor explicit `grok-4.5` | Live for **orchestrator / implement / advisory** when native dark | **Not** sealed formal CF |

**Proof command:**

```bash
.venv/bin/python -m pytest tests/test_review_isolation.py -k 'grok_isolated or oauth_store_is_never_staged' -q
```

## Written decision (stream #5512)

**Option C for now (fail-closed residual), not permanent wontfix.**

1. Inventory + fail-closed tests landed via **#5582** (merged).
2. Until OAuth can be scoped/proxied so tools only see the sealed snapshot (options A/B on #5557), **do not** flip `formal_review_eligible`.
3. **Do not** treat Cursor-pinned `grok-4.5` as sealed formal CF — it is the native-dark **orchestrator/implement** fallback only (`model_catalog` `orchestrator_seats.grok` / `grok-4.5-cursor-fallback` review ladder for *resolve-reviewer* when native is unhealthy is still subject to isolation if used as formal launch).
4. Substitute formal CF path remains the product default (below).

Revisit when: Grok CLI gains a review-only credential profile, or a proxy can mint tool-scoped tokens that cannot read host OAuth stores / primary checkout.

## Live lane (non-formal)

- `delegate.py --agent grok --model grok-4.5`
- `ai_agent_bridge ask-grok` / `ask-grok-build`
- Native Grok Build TUI / CLI cold-start
- Cursor **explicit** `--model grok-4.5` if native path dark (never Cursor `auto` as identity)
- **Orchestrator seat** (fleet-comms): same pin; requests CF via `review-pr`, does not self-seal

## Substitute formal CF

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N>              # codex / gpt-5.6-terra @ high
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> --reviewer claude  # claude-sonnet-5 @ high
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> --reviewer glm     # LOCAL-ONLY
```

## Flip criteria (do not skip)

1. Proven separation: auth works for the engine **without** tools reading host OAuth / ambient project credentials.
2. `prepare_isolated_review_launch(engine="grok")` positive path + negative tests (no auth in model-read scope; no primary checkout).
3. `review-pr --reviewer grok` **or** sealed transport registration with receipt fields (model, family=xai, harness, effort).
4. Real smoke formal CF on a non-Grok-authored PR (cross-family).
5. Then flip `formal_review_eligible: true` and enablement PR CF'd by a **non-Grok** family.

Parent: #5557 · stream #4707 · product #5512.
