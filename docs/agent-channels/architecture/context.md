# architecture — cross-cutting design decisions, refactors, ADRs

This channel is for conversations that don't fit inside one
subsystem — cross-cutting concerns like "should we rewrite X?",
"how do we version Y?", "is Z the right abstraction?". Think of it
as the ADR (Architecture Decision Record) channel.

## What lives here

- Proposed rewrites / refactors with tradeoff analysis
- Cross-cutting data model decisions
- Choice of tools, libraries, substrates (e.g. the channel bridge
  itself was debated here: file-based JSONL vs SQLite, single- vs
  multi-project, etc.)
- Integration patterns between subsystems
- Performance / scaling concerns when they affect multiple components
- Deprecation plans + migration strategies

## What does NOT live here

- Subsystem-specific bugs → #pipeline or #content
- One-off code reviews → #reviews
- Individual module build frictions → #content

## Reference

| File | What |
|---|---|
| `docs/decisions/` | Architecture Decision Records (with expiry dates) |
| `docs/best-practices/track-architecture.md` | Track layout and slugs |
| `docs/MONITOR-API.md` | Monitor API endpoints (the source of volatile state snapshots) |
| `scripts/check_decisions.py` | Alert on expired ADRs |

## Recent open threads

- **Channel bridge (#1190)** — single-project for Phase B, extract as standalone package in Phase D
- **V6 pipeline refactor (#1142)** — extract 6000-line god object into phase modules (blocked on first seminar build)
- **Diasporiana PDF ingest (#1188)** — deferred until curriculum is stable
- **Multi-project support** — deferred to Phase D after channel bridge ships
