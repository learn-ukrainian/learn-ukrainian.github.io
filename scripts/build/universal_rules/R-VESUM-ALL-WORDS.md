---
id: R-VESUM-ALL-WORDS
description: Verify every Cyrillic word form in artifacts via mcp__sources__verify_words.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: []
---

**Verify every example word in VESUM** (VESUM all-words coverage). Verify every Cyrillic word form in `module.md`, `activities.yaml`, `vocabulary.yaml`, and `resources.yaml` via `mcp__sources__verify_words`, except intentionally bad forms protected by `<!-- bad -->...<!-- /bad -->` or fields the gate excludes (`error:` / `errorWord:` in error-correction items). Selective verification is silent fabrication.

**L2-trap: over-applied reflexive -ся.** Before emitting any `-ся` form, verify it. These always fail as personal reflexives unless VESUM says otherwise: `пити → *п'юся`, `читати → *читаюся`, `писати → *пишуся`.

**Modern Ukrainian + heritage-defense discipline.** Default to post-2019 Pravopys forms. Never classify a word as Russianism/surzhyk/calque merely because it is archaic, historical, dialectal, or shares Proto-Slavic roots with Russian. Route uncertain forms through `mcp__sources__search_heritage` first (the кобета/кобіта pattern). If the form is authentic but non-standard, tag `[Archaism]` / `[Historism]` / `[Dialectism]` and give the modern equivalent. Unverified → omit or emit `<!-- VERIFY: heritage status for "X" unresolved -->`.

Use the canonical MCP names as applicable for Tier-1 checks: `mcp__sources__check_modern_form`, `search_definitions`, `search_style_guide`, `search_grinchenko_1907`, `query_pravopys`, `search_esum`, `mcp__sources__search_heritage`, `mcp__sources__search_slovnyk_me`.
