---
title: "Word Atlas (Лексикон) — V7 Design"
status: DRAFT (2026-05-23)
owner: orchestrator + user sign-off
scope: new top-level site section serving per-lemma dictionary pages from the existing sources.db + jsonl corpus
relates_to:
  - docs/best-practices/v7-design-and-corpus.md (V7 + corpus SSOT)
  - memory/MEMORY.md #M-11 (V7 design + corpus SSOT before any module work)
  - docs/session-state/2026-05-23-v7-design-alignment-m20-reverted.md (origin context)
---

# Word Atlas — V7 Design

## TL;DR

Build a **separate top-level site section** that renders one page per Ukrainian lemma using data already present in `data/sources.db` + `data/vesum.db` + `data/external_articles/*.jsonl` + `data/processed/esum_vol{1-6}.jsonl`. The section sits alongside the curriculum tracks (A1-C2, seminars) — it does NOT embed into lessons. Lessons cross-link into it; it cross-links back to lessons.

The editorial moat over slovnyk.me is the **decolonization layer**: sovietization flags, heritage-defense badges, calque warnings, Russian-shadow detection — all surfaced visually, all provenance-stamped, all derived from existing MCP tools.

This is V7 scope. It compounds with the writer + reviewer prompt rebuild that #M-11 mandates: once atlas pages exist, the writer's job becomes "find the lemma, link to its atlas page" instead of "remember 30 MCP tools and reproduce dictionary data inline."

## 1. Motivation

| What's true today | Why the atlas closes it |
|---|---|
| `data/sources.db` holds VESUM, СУМ-11, Грінченко, ESUM vol 1, style guide, idioms, UA-GEC, paronyms, PULS CEFR, Балла, dmklinger, literary, external articles + jsonl companions for 8 external collections | None of it is reachable by a human reader without invoking MCP tools. The data is LLM-only today. |
| The m20 revert (2026-05-23) surfaced that the writer prompt only knows ~6 of the 30+ MCP tools available | A word page is the visual proof that we have corpus depth. Once it exists, the writer prompt can be REQUIRED to deeplink to it instead of duplicating data inline. |
| slovnyk.me is the de-facto Ukrainian word-page experience | slovnyk.me is a flat aggregator with no editorial voice. We have four moats they structurally can't add: sovietization flag, heritage-defense, calque warning, course cross-link. |
| Every Ukrainian-language learner eventually opens a chronicle / poem / blog and hits an unknown word | Today our app has no answer. The atlas gives a permalink answer + a "try the lesson that uses this word" funnel back to the curriculum. |
| Per-module `vocabulary.yaml` files duplicate stress, gender, POS, examples across modules | The atlas is the canonical source. (Dedupe is a follow-up — see §10.) |

## 2. Naming + URL

Proposed: **Лексикон** (UK) / **Lexicon** (EN). Distinct from lesson Tab 2 «Словник» — no naming collision. Alternatives flagged in §11 for user decision.

URLs:

- Hub: `/lexicon/` — A-Я alphabetical index, recently-added words, search box
- Word page: `/lexicon/{lemma}` (UTF-8 Cyrillic; e.g. `/lexicon/князь`)
- Section search (v3+): `/lexicon/search?q=...`

## 3. Where it sits in the site

Top-nav gains a new top-level section parallel to the curriculum tracks:

```
Home  |  A1-C2  |  Seminars  |  Лексикон  |  About
```

Same nav-level visibility as `Seminars`. Distinct visual identity (proposed: teal-yellow gradient — distinguishes from core-blue and seminar-purple).

**Critical: the atlas is a SEPARATE section, not embedded.** Lessons link OUT to it; the atlas links BACK to lessons. Module MDX, vocab.yaml, and resources.yaml stay readable as standalone artifacts.

## 4. Page contract

Sections, in flow (top-to-bottom). Each section is OMITTED if it has no data — never shown empty. Every section carries a provenance footer (source dictionary + URL where available).

| # | Section | Source(s) | Visual primitive (reused from PoC) |
|---|---|---|---|
| 1 | **Шапка** | header derived from VESUM + stress dict + PULS CEFR + heritage status | hero gradient (atlas-specific colors) |
| 2 | **Значення** | СУМ-20 (slovnyk.me) → Грінченко 1907 → СУМ-11 (sovietization-flagged per entry) | definition cards; sovietized entries get red badge |
| 3 | **Етимологія** | ESUM vol 1-6 jsonl | reused from PoC #27 EtymologyTrace pattern (`.ety-stage` / `.ety-arrow`) |
| 4 | **Морфологія** | VESUM | paradigm table (case×number for nouns; person×number×tense for verbs; etc.) |
| 5 | **Походження + статус** | `mcp__sources__search_heritage` merger | classification badge: authentic / Russianism / surzhyk / dialect / borrowing / archaism / historism |
| 6 | **Стилістичні нотатки** | Антоненко-Давидович (structured + prose) + UA-GEC error pairs | yellow `.rule-box` for calque warnings; example error→correction pairs |
| 7 | **Синоніми + антоніми** | `mcp__sources__search_synonyms` (WordNet) | chip layout (reused from `.groupsort-chip`); "auto-translated, audit pending #1657" caveat badge |
| 8 | **Фразеологізми** | `mcp__sources__search_idioms` (Фразеологічний 25K) | idiom cards |
| 9 | **Літературні засвідчення** | `mcp__sources__search_literary` (125K chunks — chronicles, poetry, legal) | purple `.source-box` pattern (reused from PoC seminar) |
| 10 | **Підручники** | `mcp__sources__search_text` (textbooks 23K) | resource cards with grade + page + chunk |
| 11 | **Зовнішні матеріали** | `mcp__sources__search_external` grouped by collection (`ulp_blogs`, `ulp_youtube`, `pohribnyi_pronunciation`, `istoria_movy`, `realna_istoria`, `komik_istoryk`, `imtgsh`, `other_blogs`) | resource cards per collection, with media-type tag |
| 12 | **Курсові посилання** | scan of `curriculum/l2-uk-en/{level}/{slug}/vocabulary.yaml` | "Used in: A1 M08 (Things Have Gender), HIST M23 (Danylo)" — cross-link back to lessons |
| 13 | **Переклад** | Балла EN→UK + dmklinger UK→EN | translation pairs |
| 14 | **Wikipedia** | `mcp__sources__query_wikipedia` | summary card for proper nouns / concepts |
| 15 | **Метадані** | aggregation of all above | provenance footer: source URLs, freshness timestamp, "report data error" link |

## 5. Decolonization editorial layer (the moat)

Each editorial signal maps to an existing PoC visual primitive — no new components needed:

| Editorial signal | Visual treatment | PoC pattern reused | Trigger |
|---|---|---|---|
| **Sovietization warning** | red `.myth-box` at top of any СУМ-11 entry with `risk≥1` | myth-box | `sovietization_risk` field from `search_definitions` |
| **Heritage-defense success** | green inverted myth-box at top of «Походження» | myth-box (green variant) | `search_heritage` returns `is_russianism=false` + pre-Soviet attestation |
| **Calque warning** | yellow `.rule-box` with header «Можлива калька» | rule-box | Антоненко-Давидович structured OR prose entry hits this lemma |
| **Russian morphological shadow** | red inline pill on header | (new minimal addition) | `check_russian_shadow` returns true |
| **Recent borrowing** | blue inline pill on header | (new minimal addition) | ESUM marks ≥19th-century borrowing |
| **Dialect / regional** | teal inline pill on header | (new minimal addition) | `search_heritage` attaches `classification=dialect` |

Provenance discipline: every badge cites the specific tool result that triggered it. Click the badge → tooltip with the dictionary entry that grounds the classification. No badges fired by heuristics; only by tool results.

## 6. Data model

Per-lemma canonical record. Cached as `data/lexicon/{lemma}.json` for static build (v1+) OR computed on-demand (v0/v3+ long tail):

```yaml
lemma: князь
canonical_form: князь
pos: noun
gender: m
animacy: anim
stress: кня́зь
cefr_level: B2  # from puls_cefr; nullable
heritage_status:
  classification: authentic-oes
  pre_soviet_attestation: ["grinchenko_1907", "esum"]
  is_russianism: false
sovietization_risk: 0
russian_shadow: false
calque_warning: null
sections:
  definitions:
    - source: sum20
      text: "..."
      url: "https://slovnyk.me/dict/newsum/князь"
      sovietization_risk: 0
    - source: grinchenko_1907
      text: "..."
      url: null
    - source: sum11
      text: "..."
      sovietization_risk: 0
      sovietization_keywords: []
  etymology:
    - period: "Прагерманська"
      form: "*kuningaz"
      note: "Germanic origin; borrowed into Proto-Slavic via Gothic."
      source: esum
    - period: "Праслов'янська"
      form: "*kъnędzь"
      note: "Sound shift: u>ъ, g>z>dz>z."
      source: esum
    # ... etc
  morphology:
    paradigm:
      singular:
        nom: князь
        gen: князя
        dat: князеві / князю
        acc: князя
        ins: князем
        loc: князеві / князі
        voc: князю
      plural:
        nom: князі
        # ...
    source: vesum
  literary:
    - author: "Літописець"
      work: "Галицько-Волинський літопис"
      line: "Данило ж, князь добрий, хоробрий і мудрий..."
      url: null
      source: literary_fts
  textbooks:
    - source_file: "kravtsova-history-grade-7"
      page: 84
      chunk: "..."
  external:
    ulp_blogs: []
    ulp_youtube: [...]
    pohribnyi_pronunciation: []
    istoria_movy: [...]
    realna_istoria: [...]
    komik_istoryk: []
    imtgsh: []
    other_blogs: []
  course_usage:
    - track: hist
      module_num: 23
      slug: danylo-halytskyi
      lesson_gloss: "prince, ruler of a principality"
  translation:
    en: ["prince", "duke", "ruler"]
    source: balla
  wikipedia:
    summary: "..."
    url: "https://uk.wikipedia.org/wiki/Князь"
generated_at: "2026-05-23T..."
sources_used: [vesum, sum20, grinchenko_1907, esum, literary_fts, balla, query_wikipedia]
```

## 7. Integration with V7 pipeline (separate but cross-linked)

The atlas is its own section. It does NOT embed into lessons. But the V7 pipeline gains awareness of it.

### Writer prompt directive (added during the prompt rebuild that #M-11 mandates)
> "When introducing a vocabulary item, link to `/lexicon/{lemma}` rather than expanding its etymology, paradigm, sovietization status, or heritage notes in `module.md`. The atlas holds that data; `module.md` is the lesson — not the dictionary. This frees you to focus on lesson-specific examples and pedagogical sequencing."

Effect: writer's prompt-space shrinks. Fabrication paths close (writer can't invent etymology because it's no longer their responsibility).

### Reviewer prompt audit (added during reviewer rebuild)
> "For each vocabulary item in the module, verify a matching atlas page exists OR is queued for generation (`data/lexicon/_queue.txt`). If atlas data conflicts with the writer's lesson-specific gloss / example, flag as `content_vs_canonical_mismatch`."

Effect: lesson-canonical drift is caught deterministically.

### Lesson Tab 2 VocabCard
Existing `<VocabCard>` gains a "more →" link to the atlas page. Card itself stays minimal (lemma + lesson-gloss + lesson-example). Tap → full atlas page.

### Lesson Tab 4 Resources
`format_resources_for_mdx()` gains a "Related lexicon entries" subsection listing atlas links for every vocab item in the module. This is one of the things that makes Tab 4 cite the corpus — atlas entries ARE corpus citations.

### MDX assembler
No new transforms required for v0. Atlas links are plain Markdown links; Starlight rendering handles them.

## 8. Gates / quality floors (deterministic, not LLM)

| Gate | Rule | Failure mode |
|---|---|---|
| `lemma_in_vesum` | Every atlas page MUST exist as a lemma in VESUM | 404 if not (no orphan pages) |
| `provenance_per_section` | Every section MUST cite a source + URL where the dictionary has one | missing provenance fails the build |
| `section_omitted_not_empty` | Sections with no data are OMITTED, not rendered empty | empty section in HTML fails the gate |
| `sovietization_must_be_flagged` | If `sovietization_risk≥1` for ANY rendered definition, the red editorial badge MUST appear above it | unflagged sovietized content fails the gate |
| `heritage_evidence_required` | "Authentic Ukrainian" badge requires pre-Soviet attestation (Грінченко OR ESUM) cited inline | unsupported badge fails the gate |
| `cross_link_integrity` | "Used in" modules listed in section 12 must exist in `curriculum/l2-uk-en/curriculum.yaml` | broken cross-link fails the gate |
| `wiki_summary_attributed` | Wikipedia summaries cite the article URL + a freshness date | missing attribution fails the gate |

These are deterministic checks. No LLM in the rendering path. The atlas is a function of the data.

## 9. Phases

| Phase | Scope | Lemma count | Effort |
|---|---|---|---|
| **v0 (this PoC)** | render 1 page hand-built for design review (`князь`, `прапор`, `файний` showcased in one HTML file with a switcher) | 3 (visual) | this design package |
| **v1** | render m20 (a1/my-morning) + m1 (a1/sounds-letters) + m08 (a1/things-have-gender) vocabulary lemmas via Astro dynamic route | ~80 | 1-2 days |
| **v2** | scale to A1+A2+B1 curriculum-referenced lemmas (intersected with `puls_cefr` + frequency) | ~3-5K | ~1 week |
| **v3** | alphabetical hub page (`/lexicon/`) + search UI + section anchor links | same lemma set | 3-5 days |
| **v4** | audio (TTS or recorded), editorial overrides (`data/lexicon_overrides/{lemma}.yaml`), "report data error" form | same | future |
| **v5** | full scale: A1-C2 + seminars + extended PULS CEFR + ESUM vols 2-6 | ~10K+ | future |

## 10. Not in scope (v0/v1)

- **Module `vocabulary.yaml` dedupe against atlas** — substantial schema migration; queued as a follow-up
- **Audio pronunciation** (v4)
- **Editorial overrides** — human-curated notes layered on top of dictionary data (v4)
- **Search UI** (v3)
- **User accounts / favorites / progress** (future)
- **Crowdsourced corrections** (future)
- **English-side reverse pages** (`/lexicon/en/prince` → atlas of Ukrainian equivalents) (future)

## 11. Open questions (user-decided)

1. **Section name** — Лексикон vs Словник (with disambiguation from Tab 2) vs Атлас слів vs Корпус. Recommendation: Лексикон.
2. **URL scheme** — `/lexicon/{lemma}` (Latin path + Cyrillic lemma) vs `/слова/{lemma}` (full Cyrillic). Recommendation: `/lexicon/{lemma}` — best SEO + tooling compatibility.
3. **Pre-build vs on-demand rendering** — Astro static-build (v1-v2) vs Cloudflare Worker rendering (v3+ long tail). Recommendation: static for v1-v2, evaluate at v3 once we know the long-tail size.
4. **Cross-link integrity gate** — warn or hard-fail on broken atlas links from module MDX? Recommendation: warn at v1, hard-fail at v2.
5. **Editorial overrides storage** — `data/lexicon_overrides/{lemma}.yaml` layered on top of generated data? (v4 question.)

## 12. Visual reference

HTML PoC: [`docs/poc/poc-word-atlas-design.html`](../poc/poc-word-atlas-design.html)

Shows three words via a switcher (pattern reused from `poc-lesson-design.html`):

- **князь** — rich data, no editorial issues; demonstrates etymology timeline + literary attestation + course cross-link
- **прапор** — sovietization badge visible at top; demonstrates the editorial moat
- **файний** — heritage-defense badge (galicianism); demonstrates the "authentic Ukrainian heritage" classification

Every visual primitive reuses `poc-lesson-design.html` CSS — hero gradient (with new atlas-specific colors), `.rule-box`, `.myth-box`, `.source-box`, `.exercise`, `.vocab-table`, `.groupsort-chip`, `.ety-stage`, etc. The atlas feels like part of the same product, not a separate app.

## 13. Companion changes (informed by atlas, but tracked separately)

Per #M-11 + the m20 revert, writer + reviewer + MDX assembler still need their rebuilds. The atlas REDUCES the surface area of those rebuilds:

- Writer no longer needs to know 30 MCP tools — it knows "find the vocab item, link to `/lexicon/`, done."
- Reviewer no longer needs to recompute sovietization / heritage checks per module — it cross-references the atlas page's badge.
- MDX assembler gains zero new transforms in v0; gains "Related lexicon entries" subsection generator in v1.

These changes are tracked in the upcoming writer + reviewer prompt rebuild design doc (to follow once this design is approved).
