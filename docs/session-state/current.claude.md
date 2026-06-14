# Current — Claude Session Handoff (2026-06-14)

> Router: read `docs/session-state/current.md` first.
> **Latest detailed handoff: `docs/session-state/2026-06-14-claude-s6-calque-integrated-stale-server-fix-reenrich.md`** — read top-to-bottom.
>
> **✅ Shipped (merged to main):** #3110 — §6 grok-swarm calque integration (`PHRASAL_CALQUES` +6, new `SENSE_RESTRICTED_CALQUES` polyseme bucket +5, regression test) + a Content-Gate dossier-wordcount scope fix. Plus an operational fix: restarted the stale `sources` MCP server so the #3101 `tag_filter` fix is live.
>
> **🔄 RESOLVE FIRST:** the controlled **Atlas re-enrich** is in flight (bg `enrich_manifest.py`, was PID 94346 — silent, writes manifest at end). On completion run `/tmp/atlas-spotcheck.py` and **commit `site/src/data/lexicon-manifest.json` ONLY if `VERDICT: CLEAN`** (#M-11; auto-deploys). Baseline: synonyms 21 / wiki 0 / etymology 1165 → expect synonyms ≫21 + wiki >0.
>
> **🎯 Then:** §6 enrich wiring (#3098) — brief ready at `/tmp/s6-calque-wiring-brief.md`; **de-risked to ~1 card today** (only `виглядати` of 37 dataset keys is in the A1 manifest), so LOW urgency. Then #3102 nice-to-haves (fold into that dispatch) + #3106 sources.db backfill.
>
> Prior handoff (superseded): `2026-06-14-claude-grok-build-validation-atlas-quality-queue.md`.
