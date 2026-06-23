# Lexicon manifest scaling — defer re-architecture until scale demands

**Date:** 2026-06-23 · **Status:** Decided (deferred) · **Lane:** infra/Atlas

## Decision
Keep the **single JSON manifest** as-is for now. Do NOT shard or migrate yet. Revisit
when scale actually pushes the build toward its ceiling.

## Context
- Manifest today: ~4,148 entries / 39 MB (~9.3 KB/entry, fat enrichment). Hydrated from a
  GitHub Release asset (#3659), not committed. It is a **build input**, not served to clients.
- Projected: curriculum alone → 20k+; with readings → 30–50k (≈186–466 MB).
- Host is **GitHub Pages (static, no backend)**. Vercel/serverless explicitly off the table for now.
- Build runner: `ubuntu-latest` (16 GB RAM / 4 vCPU), Node 22, **no `--max-old-space-size`** →
  V8 ~4 GB heap default is the real near-term ceiling.

## Agreed direction WHEN we get there (not now)
The pain is build memory (every page route `import`s the whole manifest) + the monolithic
browse page + the growing search index — NOT client downloads, NOT git size. Fix by **splitting
by consumer**, all static (no backend needed):
- Per-word pages → Astro content collection / per-letter routes so each build slice loads only its part.
- Browse → static per-letter shards (browser fetches `<letter>.json`).
- Search → **Pagefind** (static sharded index + in-browser client; built for static hosts).
- Canonical store stays JSON unless the build genuinely chokes; SQLite-as-build-time-store is an
  option (it is NOT a backend — queried in CI only) but adds moving parts.

## Triggers to revisit
- Entry count approaching ~10–15k, OR
- A Pages build redlining memory/time (stopgap first: `NODE_OPTIONS=--max-old-space-size=8192`), OR
- Turning on periodic auto-grow (which is what pushes entry counts up) — design this before grow ramps.

## Cheap stopgap (one line, when needed)
`NODE_OPTIONS=--max-old-space-size=8192` in the Pages build step buys headroom before any re-architecture.
