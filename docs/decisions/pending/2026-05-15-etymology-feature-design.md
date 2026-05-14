# DECISION REQUIRED — Etymology feature design (public static feature for github.io)

**Status:** PROPOSED 2026-05-15
**Surfaced:** Continuation of `docs/session-state/2026-05-14-etymology-feature-handoff-brief.md` (user direction at 2026-05-14 session close).
**Scope:**
- IN: `scripts/etymology/` (page generator, search index builder, explorer dataset builder), `starlight/src/content/docs/etymology/` (29k MDX pages output), `starlight/src/pages/etymology/explore.{astro,client.js}` (interactive explorer), Decision Card itself.
- OUT (this PR family): LLM-assisted cognate extraction backfill (Phase 4, only if v1 quality is insufficient), Antonenko / Грінченко heritage-crossover callouts (Phase 4), translation of explorer UI to EN/UK toggle.

---

## TL;DR — three decisions, all decidable inline

The 2026-05-14 etymology brief flagged three open design questions. Two have clearly dominant answers; the third has a recommended path + cheap fallback. None require multi-agent dispatch.

| Question | Decision | Why |
|---|---|---|
| **Q1.** Structured cognate extraction (LLM) vs raw text vs heuristic regex? | **Heuristic regex** for v1 (with LLM fallback as Phase 4 backfill if needed). | ESUM's etymology text follows a consistent template (`р. сéрдце, бр. се́рца, п. serce, ...`). Language markers are already extracted into the `cognates` JSON column (✓). The follow-form regex is a 30-line script, costs $0, builds in minutes. LLM extraction is a one-time ~$5-50 spend that we don't need to lock into v1. |
| **Q2.** Slug strategy — ASCII transliteration vs Cyrillic? | **ASCII transliteration** (BGN/PCGN romanization), with case-insensitive lookup and a Cyrillic alias map server-side. | URL portability dominates: ASCII slugs work in any context (shells, Twitter, search engines). Cyrillic URLs have edge-case failures (Twitter strips, some markdown previewers fail, copy-paste loses encoding). Aliases give us the Cyrillic friendly-name when someone types it. |
| **Q3.** Explorer bundle — single file vs lazy-load? | **Single compact bundle** (cognate-essentials only, ~1-2 MB gzipped), per-lemma raw etymology text **lazy-fetched** from the static MDX pages on click. | 25,205 unique lemmas × ~200 bytes for cognate essentials ≈ 5 MB raw / ~1.5 MB gzipped. Tolerable single-page load. Full etymology text (~500-2000 bytes each) only needed when user clicks a node — fetch on demand from the corresponding static page. |

**No Decision Card is BLOCKING.** Implementation proceeds in parallel with this card sitting in `pending/`. User can REVISE the proposals when they have a chance; implementation follows the proposed path until told otherwise.

---

## Q1 — Cognate extraction strategy

### Data shape today (from `data/sources.db`)

```sql
-- esum_etymology_meta.cognates is already JSON-stringified language abbreviations:
sqlite> SELECT lemma, cognates FROM esum_etymology_meta WHERE lemma='дім';
дім|["псл.", "іє.", "дінд.", "ав.", "лит.", "гр.", "лат.", "гот.", "стел.", "др.", "р.", "бр.", "п.", "ч.", "слц.", "болг.", "схв.", "слн."]
```

The MARKERS are extracted; the FORMS (`сердце`, `serce`, `srdce`) are not. We need forms to render a cognate tree.

### Options considered

| Option | Quality | Cost | Time-to-ship |
|---|---|---|---|
| A. Heuristic regex (`<marker>\\s+(\\w+(?:\\s+\\w+)?)`) | ~80% (template matches; misses re-orderings, parens, multi-word entries) | $0 | ~30 LOC, ~1 min build |
| B. LLM extraction (Gemini Flash, build-time) | ~95% (handles re-orderings, parens, parenthetical glosses) | ~$5-50 one-time (25,205 entries × 200-2000 tokens) | ~30-min build, $$ |
| C. Raw text only (no structured cognate extraction) | N/A — explorer becomes a search-only browse view | $0 | shortest, no explorer at first ship |

### Decision: **Option A (heuristic regex) for v1**

Rationale:
- ESUM has consistent template. The regex `<marker> +<form>(,| \\(|$)` captures the dominant case.
- The `cognates` JSON column already tells us WHICH markers exist per lemma → we know what to search for.
- Failure mode is graceful: when regex doesn't match, the entry shows raw etymology text. No worse than option C.
- Option B is a backfill PR (one prompt, one Gemini dispatch when we have evidence v1 quality is insufficient).
- Option C **violates the user's "both A and B at first ship" constraint** — the explorer needs SOMETHING structured to render branches.

### What ships
- `scripts/etymology/extract_cognate_forms.py` — reads `esum_etymology_meta`, regex-parses cognate forms from etymology_text using the existing markers, emits a new JSON column or sidecar table `esum_cognate_forms`.
- Output shape:
  ```json
  {"lemma": "серце", "vol": 5, "page": 271, "cognate_forms": {
    "р.": "сéрдце", "бр.": "се́рца", "п.": "serce", "ч.": "srdce", ...
  }}
  ```
- Coverage telemetry: emit `cognate_extraction_coverage.json` reporting how many entries got at least 1 form per marker. <50% coverage → escalate to Option B before public ship.

---

## Q2 — Slug strategy

### Options

| Option | URL | Pros | Cons |
|---|---|---|---|
| A. ASCII transliteration | `/etymology/sertse/` | Portable everywhere; SEO-friendly; clean | Less authentic; needs alias map for Cyrillic search |
| B. Cyrillic URL | `/etymology/серце/` | Authentic; direct lemma in URL | Twitter strips; some tools fail; copy-paste loses encoding |
| C. Numeric ID | `/etymology/5-271/` | Disambiguates polysemy trivially | Opaque; not shareable |

### Decision: **Option A (ASCII transliteration via BGN/PCGN)**

The transliteration map: standard BGN/PCGN with simplifications (no apostrophes, no double-letter for `ь`/`ъ`, ASCII-only output).

```
а→a  б→b  в→v  г→h  ґ→g  д→d  е→e  є→ie  ж→zh  з→z
и→y  і→i  ї→i  й→i  к→k  л→l  м→m  н→n  о→o  п→p
р→r  с→s  т→t  у→u  ф→f  х→kh ц→ts  ч→ch ш→sh щ→shch
ь→   ю→iu я→ia ' →
```

Polysemy disambiguation: when 2+ entries share a slug, append `-<vol>-<page>`:
- `/etymology/maty/` → primary (vol 2, page 48)
- `/etymology/maty-2-271/`, `/etymology/maty-3-412/` → secondary

A landing card at `/etymology/maty/` lists the three entries with semantic differentiation summaries.

### Cyrillic alias map

Build-time we emit `etymology_aliases.json` mapping Cyrillic → ASCII slug. The search index uses both. The explorer accepts either as a query.

Server-side redirect: NOT needed (github.io is static). Client-side router handles `/?q=серце` → `/etymology/sertse/` redirect.

---

## Q3 — Explorer bundle strategy

### Options

| Option | Bundle size | First paint | Click-through latency |
|---|---|---|---|
| A. Single compact bundle (cognate essentials) | ~1.5 MB gzipped | 1-3s on 3G, instant on cable | Instant (data already loaded) |
| B. Lazy-load by first letter | ~30-50 KB initial, fetch on type | <500ms | 100-300ms per letter |
| C. Full bundle (raw etymology + cognates) | ~5 MB gzipped | 3-10s on 3G | Instant |

### Decision: **Option A (compact single bundle for cognate tree, raw text lazy-fetched on click)**

Rationale:
- 1.5 MB gzipped is a normal-sized React bundle; modern users tolerate it for a feature-rich page.
- Click-to-recenter the tree needs cognate data INSTANTLY → lazy-load by letter introduces 100-300ms gates per click which feels broken.
- Raw etymology text is BIG (500-2000 bytes × 25k = 13 MB) — that DOES need lazy-load. Fetch the corresponding static MDX page when the user clicks "Read full etymology."

### Bundle shape

```js
// /etymology/explore.dataset.json (one bundle, ~1.5 MB gzipped)
{
  "version": "2026-05-15-v1",
  "lemmas": {
    "sertse": {
      "lemma": "серце",
      "vol": 5, "page": 271,
      "cognates": {"р.": "сéрдце", "п.": "serce", "ч.": "srdce", "бг.": "сърце"},
      "proto": "*sьrdьce",
      "heritage": []
    },
    "maty-2-48": { ... },
    ...
  }
}
```

Raw etymology text NOT in bundle — fetch `/etymology/sertse/raw.json` (or just parse `/etymology/sertse/` MDX page on click) when user clicks "Full etymology."

### Tech stack
- D3.js force-directed graph for the tree (smooth recenter animation)
- Lunr (or FlexSearch) for client-side typeahead — already-precomputed inverted index in the bundle
- No framework needed for the explorer page; vanilla React or Solid for state management

---

## What ships in this PR family (sequenced)

1. **PR A — Decision Card + Phase 1 (this card lands as PROPOSED)** [~30 min]
   - This file in `docs/decisions/pending/`.
   - `scripts/etymology/extract_cognate_forms.py` — regex-extract forms from etymology_text, emit `esum_cognate_forms` sidecar table.
   - `scripts/etymology/extract_static_pages.py` — emit one MDX per lemma into `starlight/src/content/docs/etymology/`.
   - `scripts/etymology/transliterate.py` — Ukrainian-to-ASCII BGN/PCGN transliteration helper + tests.
   - Run on full 25k unique-lemma corpus, verify Astro build succeeds with the new pages.
   - Astro `getStaticPaths` for `/etymology/[slug]/`.
   - **Smoke test**: open `/etymology/sertse/` locally, confirm content renders.

2. **PR B — Phase 2 search + landing** [~1-2 hours]
   - `/etymology/` landing page (A-Z browse, search bar).
   - Lunr index built at build-time (`extract_search_index.py`).
   - Client-side typeahead component.

3. **PR C — Phase 3 explorer** [~3-6 hours]
   - `extract_explorer_bundle.py` emits the compact JSON.
   - `/etymology/explore/` page (D3 + Lunr + state).
   - Mobile-responsive (vertical timeline fallback).

4. **PR D — Phase 4 backfill (only if quality demands)** [TBD]
   - LLM-assisted cognate extraction for entries where regex coverage <80%.
   - Antonenko `style_guide` cross-link callouts.
   - Грінченко heritage badges.

---

## Open questions for user (NOT blocking)

The user can REVISE any of these after-the-fact; implementation proceeds on the proposed defaults.

1. **Navigation placement.** Etymology lives at `/etymology/` — should it be exposed in the top nav, side nav, or only via the curriculum-page "Want to know where this word comes from?" widget? **Default: top nav** alongside Practice/Curriculum/About.
2. **Public vs hidden initially.** Ship to `learn-ukrainian.github.io/etymology/` publicly at first ship, or hidden behind `?preview=1` flag for a week of self-review? **Default: public ship at first PR** — user direction was "available from the beginning."
3. **Performance budget.** Astro build with 25k MDX pages — if cold-start build time exceeds 5 min, do we tier-split (build only first 5k for first ship)? **Default: try full 25k first**, escalate to tier-split only if measured.

---

## Trade-offs accepted

- **Heuristic regex misses ~20% of cognate forms.** Acceptable for v1; Option B backfill remains available.
- **ASCII slugs lose authenticity for Cyrillic-first users.** Mitigated by alias map + Cyrillic-as-display-text in page content.
- **1.5 MB bundle is heavy for mobile-3G.** Mitigated by progressive enhancement: typeahead + per-lemma pages work without the explorer bundle.

---

*Decision Card per `docs/decisions/pending/README.md`. PROPOSED 2026-05-15 by orchestrator. Awaiting user signoff for ACCEPTED; implementation proceeds on proposed defaults per #M-6 (drive don't defer).*
