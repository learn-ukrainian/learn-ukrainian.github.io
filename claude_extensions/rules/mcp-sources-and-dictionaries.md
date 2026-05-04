---
paths:
  - "scripts/**"
  - "curriculum/**"
  - "data/**"
---

# MCP Sources Tools

> The project's MCP server at port 8766 is called **`sources`** — it serves
> SQLite FTS5 indices over textbooks, literary works, dictionaries, VESUM,
> and Wikipedia. Historically called the "RAG server" — the current
> implementation is not vector-based retrieval, so the name was misleading
> and was retired. All tool prefixes are now `mcp__sources__*`. The old
> prefix `mcp__rag__*` may still appear in archived orchestration prompts
> but is no longer the canonical name.

## Core tools (always use)
- `mcp__sources__verify_word` / `mcp__sources__verify_words` / `mcp__sources__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms)
- `mcp__sources__search_sources` — **PREFERRED unified entry point** across textbooks, literary corpora, Wikipedia, external articles, and `ukrainian_wiki`
- `mcp__sources__search_text` — textbook content search (23K chunks, Grades 1-11)
- `mcp__sources__search_images` — textbook image search (14K images)
- `mcp__sources__search_literary` — primary literary sources (125K chunks — chronicles, poetry, legal texts)
- `mcp__sources__query_pravopys` — Ukrainian orthography rules (Правопис 2019)
- `mcp__sources__query_wikipedia` — Ukrainian Wikipedia

> Start with `mcp__sources__search_sources` for general retrieval. Keep `mcp__sources__search_text` for explicit textbook-only scoping when you do not want literary, Wikipedia, external, or `ukrainian_wiki` results mixed in.

## Dictionary tools (for quality and vocabulary)
- `mcp__sources__search_style_guide` — Антоненко-Давидович (279 entries indexed of ~600+ in source — completion tracked in #1663) — **calques and Russianisms**. HIGH PRIORITY.
- `mcp__sources__query_cefr_level` — PULS CEFR vocabulary (5.9K words, A1-C1) — check level-appropriateness
- `mcp__sources__search_definitions` — СУМ-11 (127K entries) — Ukrainian explanatory dictionary. **⚠️ Partially Sovietized for ideological terms** — see "Sovietization caveat" below. Each result row carries `sovietization_risk` (0/1/2) and `sovietization_keywords`.
- `mcp__sources__search_grinchenko_1907` — Грінченко (67K entries) — historical Ukrainian dictionary from 1907. Use for pre-Soviet usage attestation; **NOT for word origins/etymology** — that's a separate concern handled by `search_esum` below.
- `mcp__sources__search_esum` — ЕСУМ etymological dictionary — canonical name for ЕСУМ. PoC scope: vol. 1 (А–Г) only; vols. 2–6 are follow-up (#1662). Falls back to a goroh.pp.ua hint if word not found.
- `mcp__sources__search_idioms` — Фразеологічний (25K entries) — Ukrainian idioms and expressions
- `mcp__sources__search_synonyms` — Ukrajinet WordNet (122K synsets) — synonyms, antonyms. **⚠️ Synsets are largely auto-translated from Open English WordNet** per upstream README — quality audit pending (#1657 Tier 3).
- `mcp__sources__translate_en_uk` — Балла EN→UK (79K entries) — English→Ukrainian translations. One-way only; UK→EN reverse not yet built.

## Sovietization caveat (СУМ-11) — issue #1659

СУМ-11 (1970–1980) is the only modern-era Ukrainian explanatory dictionary
in our MCP, but it was published under late-Soviet editorial policy and
contains ideologically framed definitions for politically loaded headwords.
Empirically: **7,152 of 127,069 entries (~5.6%) are flagged** by the
sovietization scan (755 high-risk, 6,397 low-risk). High-risk examples
include `ленінізм`, `прапор`, `партійний`, `школа`, `центр`, `шлях` —
even neutral terms have Soviet citations woven into their definitions.

Every `search_definitions` result row carries:

- `sovietization_risk` — 0 (clean), 1 (keyword match in definition or
  text), 2 (high — Soviet-ideology framing opener OR ≥3 distinct keyword
  stems matched).
- `sovietization_keywords` — comma-separated stems that triggered the
  flag (e.g. `ленін,радянськ,соціалістичн`).

**When `sovietization_risk > 0` for a curriculum-content lookup:**

- Do NOT reproduce the definition verbatim.
- Prefer Грінченко (`search_grinchenko_1907`) for the same headword if it has
  pre-Soviet coverage.
- After СУМ-20 lands (#1667), prefer that for modern definitional baseline.
- If neither alternative is available, paraphrase neutrally and flag in
  reviewer evidence.

The scan is reproducible:
`.venv/bin/python scripts/audit/sum11_sovietization_scan.py --db data/sources.db`.
Audit report at `audit/sum11_sovietization_scan_<DATE>.md`.

## Dictionaries (local, in sources.db or SQLite)

| Dictionary | Entries | Type | Collection/File |
|-----------|---------|------|-----------------|
| **VESUM** | 409K lemmas, 6.7M forms | Morphological (POS, gender, inflections) | `data/vesum.db` (SQLite) |
| **СУМ-11** | 127K (7,152 flagged Sovietized — #1659) | Ukrainian explanatory (definitions, citations) | `data/sources.db` FTS5 |
| **Грінченко** | 67K | Historical Ukrainian (1907, lexicographic) | `data/sources.db` FTS5 |
| **ЕСУМ** | vol. 1 (А–Г) PoC | Etymological dictionary | `data/sources.db` FTS5 via `search_esum` |
| **Балла EN→UK** | 79K | English→Ukrainian translations | `data/sources.db` FTS5 |
| **Антоненко-Давидович** | 279 | Style guide (calques, Russianisms) | `data/sources.db` FTS5 |
| **Фразеологічний** | 25K | Ukrainian idioms and expressions | `data/sources.db` FTS5 |
| **Stress dictionary** | 2.7M forms | Word stress for annotation | via `ukrainian-word-stress` |

Source: [bakustarver/ukr-dictionaries-list-opensource](https://github.com/bakustarver/ukr-dictionaries-list-opensource) (СУМ-11, Балла, Фразеологічний)
kr-dictionaries-list-opensource) (СУМ-11, Балла, Фразеологічний)
