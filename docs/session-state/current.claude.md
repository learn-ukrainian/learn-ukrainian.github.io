# Current — Claude Session Handoff (2026-06-16 — Atlas lemma-keying + decolonization §6 SHIPPED; 7 PRs merged)

> **ROLE:** main orchestrator. User: grind issues, results-focused, use context to ~700k, **use the FLEET (#M-12)**, self-merge after fleet-review + CI-green, don't manufacture obstacles, don't idle. Quality non-negotiable.

> **State:** main moving (merge-train). Live hooks: #M-5 secret-guard + #M-0.5 admin + #M-7 pytest-push. **NEW blocking CI gate: validate_plan_ordering (#3290).** Atlas manifest = 2428 entries, §8 clean.

## ✅ SHIPPED + MERGED this session (7 PRs)
- **#3282** lxml 6.1.0→6.0.4 (deps lock; closed wrong-approach #3281).
- **#3289** chtyvo.org.ua dead-links → Wayback snapshots.
- **#3284** dmklinger gloss meta-junk cleanup (49→2 via _clean_gloss).
- **#3290** lit slug_intentional + **promote validate_plan_ordering to BLOCKING CI** (over-exemption fixed per DeepSeek). Closed #2526.
- **#3291** 32 curated homographs (gloss-disambiguated, codex-reviewed: сьома→сьомий not сім; цьому standalone) + dmklinger qualifier-prefix tail (0 residuals).
- **#3296** decolonization §6 active-participle calque layer (#3098 first slice): 20 source-verified calques, діючий sense-split fix, виглядати live SENSE-RESTRICTED card.
- **#M-5** secret-guard reactivated (earlier).
- **MILESTONES:** Atlas lemma-keying COMPLETE (T1+T2 dedup + create-case gloss/pos fix + homographs + dmklinger). Decolonization §6 moat first slice live.

## ✅ Resolved/closed
- **#3116** synonym wrong-sense over-reach — CLOSED resolved (#M-11 verified: кам'яниця/звір already removed by a prior re-enrich's sense-filter; legit dialectal кам'янка/гостинець/путівець kept). First fix attempt over-dropped (115, incl. legit вельми→дуже) — caught by a broad pre-check before any re-enrich; curated-exclusion safety-net sits on closed PR #3301 if it ever regresses.

## ⏭️ NEXT (needs fresh context / scoping / a decision — not quick grinds)
1. **#3098 broaden** (decolonization §6) — first slice (participles) shipped; broaden to collocation calques + #2156 calque-axis cross-feed. Curated-set pattern in `scripts/lexicon/calque_corrections.py`; needs a re-enrich.
2. **#2882** Atlas coverage push (BIG, multi-step): meaning ~78%, pronunciation ~71%, etymology ~62%, **synonyms ~42%**, wiki ~27%. Each field-gain = source-add + a re-enrich; scope per-field before dispatching.
3. **#3150** vocab-fingerprint: extend `manifest_fingerprint.build_fingerprint` to hash the sorted vocabulary.yaml set (so the freshness gate catches VOCAB drift, not just lexicon-code). **DECISION NEEDED:** this makes every content PR fail the freshness gate until a re-enrich is committed — confirm that workflow (or pair with an auto-regen hook = user-go) before implementing.

## ⛔ NEEDS USER
- **#2036** hermes/anthropic logged out → `hermes auth add anthropic` (OAuth) to restore the Claude-via-Hermes lane.

## Quality patterns that earned their keep this session (reuse)
- **Verify atlas merges on REAL DATA before merge** (#M-11) — caught the create-case gloss/pos mislabel + the dmklinger tail + #3116-already-resolved.
- **Cross-model review (#M-12)** — DeepSeek caught #3290 over-exemption; codex confirmed homographs; mcp__sources confirmed/fixed діучий.
- **Broad pre-check before a synonym/calque re-enrich** — apply the filter to all ~5142 synonyms + count drops; caught the #3116 over-drop (115, incl. legit вельми→дуже) before wasting a 32-min build.
- No `--admin` bypass on CI fails; root-cause + fix at the right layer (#M-0.5/#M-7).

## Atlas SSOT: `docs/atlas-data-coverage-strategy.md`. Track-owned (awareness-only): folk #3079, b1/a1/a2 content dispatches, BIO.
