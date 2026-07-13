# Current — claude-atlas role handoff (durable layer)

> Role: atlas/practice-hub lane driver (umbrella #4387, UX wave #4700).
> Launch: `./start-claude.sh --agent curriculum-orchestrator --epic atlas` — the
> SessionStart banner binds the lane (PR #5074); never self-assign "main orchestrator".
> Session-layer SSOT (gitignored, richest detail): `.claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md`.
> Thread rollover packets: `.agent/thread-rollovers/claude-atlas/` (strict continuity protocol).

## State as of 2026-07-14 (~02:30Z)

- **Relations release SHIPPED and LIVE-verified**: 8,552 entries, par/ant-bearing 266→632,
  WordNet junk retracted; site deployed twice (relations + bilingual practice glosses);
  #4946/#4951/#4966 closed with live browser evidence.
- **Open atlas follow-ups**: #5077 (enrich preserve-vs-retract semantics — the offline-strip
  landmine, full spec in issue), #5082 (homonym relation_pairs read-but-never-rendered),
  #4964 (verbatim-overlap gate — implementation started by another lane in PR #5098; two
  design asks pending under bridge task-ids `4964-design-codex` / `4964-design-grok` — read
  via `ab asks`, cross-check against #5098's approach before more design work).
- **Publish recipe hard-won mechanics** (do not relearn): index step needs
  `--db data/atlas.db`; `load_manifest()` hydrate-clobbers unrecognized local manifests
  (verify via non-default `--manifest` path; bump `generated_at` on in-flight work);
  enrich is deterministic offline; heavy atlas ops need the 32GB-gated MLX rules (#5071, merged).
- Queue candidates next: #4222/#4223 (corpus intake), #3936 (reliability tracker), #4383
  (practice drill expansion).
