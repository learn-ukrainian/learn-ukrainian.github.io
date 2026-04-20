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
- `mcp__sources__search_text` — textbook content search (23K chunks, Grades 1-11)
- `mcp__sources__search_images` — textbook image search (14K images)
- `mcp__sources__search_literary` — primary literary sources (125K chunks — chronicles, poetry, legal texts)
- `mcp__sources__query_pravopys` — Ukrainian orthography rules (Правопис 2019)
- `mcp__sources__query_wikipedia` — Ukrainian Wikipedia

> MCP `search_text` currently uses the legacy `search_textbooks` path. T1-T2 modules building via wiki compile use the new `search_sources(strategy='modern_dense_section')` path. Migration ticket TBD.

## Dictionary tools (for quality and vocabulary)
- `mcp__sources__search_style_guide` — Антоненко-Давидович (279 entries) — **calques and Russianisms**. HIGH PRIORITY.
- `mcp__sources__query_cefr_level` — PULS CEFR vocabulary (5.9K words, A1-C1) — check level-appropriateness
- `mcp__sources__search_definitions` — СУМ-11 (127K entries) — Ukrainian explanatory dictionary
- `mcp__sources__search_etymology` — Грінченко (67K entries) — historical dictionary, etymology
- `mcp__sources__search_idioms` — Фразеологічний (25K entries) — Ukrainian idioms and expressions
- `mcp__sources__search_synonyms` — Ukrajinet WordNet (122K synsets) — synonyms, antonyms
- `mcp__sources__translate_en_uk` — Балла EN→UK (79K entries) — English→Ukrainian translations

## Dictionaries (local, in sources.db or SQLite)

| Dictionary | Entries | Type | Collection/File |
|-----------|---------|------|-----------------|
| **VESUM** | 409K lemmas, 6.7M forms | Morphological (POS, gender, inflections) | `data/vesum.db` (SQLite) |
| **СУМ-11** | 127K | Ukrainian explanatory (definitions, citations) | `data/sources.db` FTS5 |
| **Грінченко** | 67K | Historical Ukrainian (1907, etymology) | `data/sources.db` FTS5 |
| **Балла EN→UK** | 79K | English→Ukrainian translations | `data/sources.db` FTS5 |
| **Антоненко-Давидович** | 279 | Style guide (calques, Russianisms) | `data/sources.db` FTS5 |
| **Фразеологічний** | 25K | Ukrainian idioms and expressions | `data/sources.db` FTS5 |
| **Stress dictionary** | 2.7M forms | Word stress for annotation | via `ukrainian-word-stress` |

Source: [bakustarver/ukr-dictionaries-list-opensource](https://github.com/bakustarver/ukr-dictionaries-list-opensource) (СУМ-11, Балла, Фразеологічний)
