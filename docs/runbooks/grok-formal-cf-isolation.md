# Grok sealed formal CF isolation (#5557)

## Status (2026-08-04 — sealed ACP route live)

The earlier Option C residual has been superseded. Grok is a live
**orchestrator / implement** seat and an eligible sealed formal CF reviewer
through the hash-pinned ACP profile. The model catalog remains the authority.

| Capability | Native Grok CLI | Formal CF sealed path |
| --- | --- | --- |
| Authentication | Cached native selector; ambient API-key selectors scrubbed | Auth material is not staged into the sealed snapshot |
| Sealed evidence | Parent-owned MCP plus hash-pinned `acpx-grok-sealed-review.md` | Only the sealed review tools are exposed |
| Sealed snapshot cwd + OS sandbox | Active through ACPX confinement | No primary-checkout or general filesystem access |
| `review-pr --reviewer grok` | Implemented | Same reservation, authority, and publication path |
| Registry `formal_review_eligible` | `true` for native `grok-4.5` | Catalog endpoint is authoritative |
| Cursor explicit `grok-4.5` | Live for **orchestrator / implement / advisory** when native dark | Still **not** sealed formal CF |

**Proof command:**

```bash
.venv/bin/python -m pytest \
  tests/agent_runtime/test_acpx_adapter.py \
  tests/ai_agent_bridge/test_review_pr.py \
  -k 'grok and sealed' -q
```

## Current decision (stream #5512)

The native Grok ACP route is eligible only when the runtime selects its
hash-pinned sealed-review profile and validates the parent-owned MCP config.
The ordinary no-tool profile remains unchanged for non-review conversations.
Cursor-pinned `grok-4.5` remains a native-dark implementation/advisory
fallback and is not an interchangeable formal-review route.

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
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> --reviewer grok    # grok-4.5 @ high
```

## Invariants

1. Grok review calls use the sealed profile only when a validated sealed MCP
   config is present; ordinary ACP calls keep the no-tool profile.
2. Ambient API-key selectors, primary-checkout access, terminal access, and
   arbitrary filesystem access remain denied.
3. The reservation and published verdict record the concrete model, xAI
   family, native Grok participant, source, and exact reviewed head.
4. Any loss of sealed-tool coverage or catalog eligibility fails closed before
   publication; it never silently falls back to Cursor.

Parent: #5557 · stream #4707 · product #5512.
