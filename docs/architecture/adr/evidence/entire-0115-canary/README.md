# Entire 0.8.42 → 0.11.5 canary receipts (#10846)

Sanitized, tracked receipts for the compatibility review recorded in
[ADR-018 § Amendment: Entire 0.11.5](../../adr-018-entire-acp-context-layer.md#amendment-entire-0115-2026-10-16).
The ADR's six-canary table points at the files that prove each row.

- `round-1/` — the first upgrade canary: hook latency for both versions,
  capture/push scenarios S0–S4, the CLI-surface probe, wrapper bytes, recall
  preflight against the real 0.11.5 binary, and mutation results. Start with
  `round-1/CANARY-SUMMARY.txt`.
- `round-2/` — the capture-guard canary after the first independent review:
  the six version-sensitive canaries through the configured, guarded entry
  points, guarded vs direct latency, wrapper regeneration round trip, and the
  round-2 mutation results. Start with `round-2/CANARY-SUMMARY.txt`.

Everything ran in a throwaway clone with local bare remotes, an isolated home
directory, no credentials and no network route; the live binary, live Entire
data and real remotes were never used. Local paths are replaced by
placeholders (`<scratch>`, `<worktree>`, `<primary>`, `<home>`), and scripts
keep a `.txt` suffix so nothing here is executable or importable.
