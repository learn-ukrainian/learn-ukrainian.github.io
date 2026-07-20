# Epic stream handoff (cross-agent)

**Issue:** #5530 · parent #5531 · long-term home: fleet-comms #5512 (Sol PR-I supervisor)

## Problem

Thread rollover packets transfer **one harness thread**. Epic session streams
transfer **driver authority for a product lane** (`epic:N`). When an interim
driver (e.g. Codex on hramatka) leaves, content dual-write alone is not enough:

- lease can stay `active` after TTL expires with a **dead PID**
- pins can still name the interim driver
- successor launched without `--epic` has no stream
- multi-packet rollover detect (#5398) can hide or mis-pick packets

## Contract (v0)

1. **Predecessor** clean-exits (`hook close`) **or** successor runs **proof-gated
   force-close** (lease expired **and** holder PID dead **and** claimer is a
   distinct live instance).
2. **Successor opens a NEW session/lease** on the same `epic:N` — never reopens a
   closed session.
3. **Pin transfer:** append a binding order that names the new driver; do not leave
   “interim until return” as the only ownership signal.
4. **Dual-write:** predecessor `STATE AT HANDBACK`; successor folds into its own
   board (e.g. `CLAUDE-DRIVER-HANDOFF.md`).
5. **Rollover:** if packets exist, bind **exact** lineage/rollover IDs. With N>1
   pending for an agent, never silent single-select (#5398).
6. **Launcher:** `--epic <name>` must set stream id + handoff slot. Note the
   slot trap: a packet under `claude/` may not appear under `claude-hramatka`.

## CLI

```bash
# Read-only diagnosis
.venv/bin/python -m agents_extensions.shared.session_streams handoff-status \
  --stream epic:4542

# Claim as Claude (force-closes expired dead holder if needed, opens session, pins)
.venv/bin/python -m agents_extensions.shared.session_streams handoff-claim \
  --stream epic:4542 \
  --agent claude \
  --harness claude-code \
  --instance-id "claude-hramatka-$(uuidgen | tr '[:upper:]' '[:lower:]')" \
  --lineage-id "lineage-epic-4542-claude-$(date -u +%Y%m%d)"
```

Exit codes: `0` ok · `2` usage · `3` stream missing · `4` refuse (live holder,
PID still up, etc.) · `5` unexpected.

## Manual checklist (until CLI is habitual)

1. `handoff-status --stream epic:N`
2. If expired + dead PID → `handoff-claim` (or force-close then open)
3. If live foreign holder → **stop** — ask that harness to close
4. Tail stream + dual-write board; fold into your handoff file
5. Launch with `--epic <name>` and bind exact rollover if any
6. Drive; dual-write after each batch; clean close on end

## Related

- `docs/runbooks/grok-session-canary.md` — end on measured rot, not compact count
- `docs/best-practices/codex-thread-handoff.md` — thread rollover (different layer)
- `.claude/<epic>-epic/TAKEOVER-PROTOCOL.md` — lane-specific interim rules (hramatka)
