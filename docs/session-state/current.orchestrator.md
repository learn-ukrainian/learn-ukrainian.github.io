# Current Orchestrator Handoff Pointer

The durable orchestrator handoff lives at:

`docs/session-state/codex-orchestrator-handoff.md`

**Latest session brief (BINDING next cold-start — fleet-comms cutovers):**

`docs/session-state/2026-07-22-fleet-comms-cutover-handoff.md`

**Primary targets (do not wait for operator to restate):**

1. Message-plane dual_write cutover after parity (#5512)
2. Retention Gate 5 — daily `retention_engine.py plan` × ≥7d before apply
3. Cold-start smoke Claude + Grok + Codex + AGY  
   Parallel: isolation fan-out #5614–#5622 (no formal_review_eligible flip without wire+CF)

`docs/session-state/current.md` may still point here for compatibility with
older cold-start hooks. Do not write detailed session state into this pointer.
