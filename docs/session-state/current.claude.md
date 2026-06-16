# Current — Claude Session Handoff (2026-06-16 — Atlas lemma-keying COMPLETE + infra grind)

> **ROLE:** main orchestrator. User: grind issues, results-focused, use context to ~700k, **use the FLEET to unblock (#M-12)**, self-merge after fleet-review + CI-green, don't manufacture obstacles. Quality non-negotiable.

> **State:** main moving (merge-train). Live hooks: #M-5 secret-guard + #M-0.5 admin + #M-7 pytest-push. **NEW blocking CI gate: validate_plan_ordering (#3290).**

## ✅ SHIPPED + MERGED this session
- **#3289** chtyvo.org.ua dead-link sweep → Wayback snapshots (live docs; bio/folk/archive left for owners).
- **#3284** dmklinger gloss meta-junk cleanup (`Alternative form of X:` → real translation) — ~49→2 via _clean_gloss reuse.
- **#3290** lit slug + **promote validate_plan_ordering to BLOCKING CI**. Over-exemption (inline+**DeepSeek** review, #M-12) FIXED: 10 LEGACY_SLUG→slug_intentional markers, c1/review-c1-5 added to curriculum.yaml, c2 pobut = 1 documented planned-unbuilt exemption, LEGACY_FIELD doc-commented. Closed #2526.
- **#2732 part1** lxml 6.1.0→6.0.4 (#3282); closed wrong-approach #3281.
- **#M-5** secret-guard reactivated.
- **ATLAS LEMMA-KEYING COMPLETE:** #3277 (T1+T2 dedup + create-case gloss/pos-null fix) + **#3291** (32 curated homographs, gloss-disambiguated + codex-reviewed: сьома→сьомий NOT сім, друга→друг NOT другий; цьому standalone) + dmklinger tail (мечеть/паска, 0 residuals). Manifest 2428 entries, §8 0 violations.

## 🟢 IN FLIGHT
- **#3291 MERGED** (homographs + dmklinger tail) — real-data verified (#M-11: all 32 folds correct, 0 meta-junk residuals). Lemma-keying milestone CLOSED.
- **#3098** (decolonization §6 active-participle calque layer — HIGHEST mission value) — PR #3296, REVIEWED (#M-4 via mcp__sources): 20 curated calques, evidence REAL (Antonenko p101 «Працюючий … працівник» confirmed verbatim; textbook corrections match), no over-flag (no блискучий/колючий traps), heritage-guard clears all. Fixed 1 entry: діючий was only «чинний» → sense-split «чинний (закон) / активний (вулкан)» per Avramenko Grade-7. Re-enrich `bo33qy9ml` running → verify §8 + commit + merge. NOTE: 0/20 calque forms are in current atlas vocab → §6 cards ARMED-but-inert on pages now; live value = lesson Russianism-flag cross-feed (#2156) + future vocab.

## ⏭️ QUEUED (atlas pipeline is SERIAL — one re-enrich at a time, #M-9)
1. **#3098 integration** — review curated set → integrate → re-enrich → merge.
2. **#3116** synonym wrong-sense over-reach (кам'яниця in шлях, звір in річка — adjacent-synset headword slips past sense-filter; enrich_manifest.py:~973). LOW (2 of 794). Fix = per-candidate sense-validation OR curated stoplist. Needs a re-enrich.
3. **#2882** umbrella Atlas coverage push (meaning 77%, pronunciation 71%, etymology 62%, synonyms 42%).
4. **#3150** vocab-fingerprint extension (make the freshness gate catch vocab drift, not just lexicon-code) — design + the re-enrich-per-content-PR tradeoff; possibly needs a hook (user-go).

## ⛔ NEEDS USER
- **#2036** hermes/anthropic logged out → `hermes auth add anthropic`.

## Notes
- Cross-model review (#M-12) earned its keep twice this session: DeepSeek confirmed the #3290 over-exemption; codex confirmed 31/33 homographs. Use it for gate/exemption/merge-confidence calls.
- Atlas SSOT: `docs/atlas-data-coverage-strategy.md`. Track-owned (awareness-only): folk #3079, b1/a1/a2 content dispatches, BIO.
