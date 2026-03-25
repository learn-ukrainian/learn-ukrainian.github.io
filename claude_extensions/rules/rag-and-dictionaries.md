---
paths:
  - "scripts/**"
  - "curriculum/**"
  - "data/**"
---

# RAG Tools (MCP)

## Core tools (always use)
- `mcp__rag__verify_word` / `mcp__rag__verify_words` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms)
- `mcp__rag__search_text` — textbook content search (23K chunks, Grades 1-11)
- `mcp__rag__search_images` — textbook image search (14K images)
- `mcp__rag__search_literary` — primary literary sources (125K chunks — chronicles, poetry, legal texts)
- `mcp__rag__query_pravopys` — Ukrainian orthography rules (Правопис 2019)
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia

## Dictionary tools (for quality and vocabulary)
- `mcp__rag__search_style_guide` — Антоненко-Давидович (279 entries) — **calques and Russianisms**. HIGH PRIORITY.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words, A1-C1) — check level-appropriateness
- `mcp__rag__search_definitions` — СУМ-11 (127K entries) — Ukrainian explanatory dictionary
- `mcp__rag__search_etymology` — Грінченко (67K entries) — historical dictionary, etymology
- `mcp__rag__search_idioms` — Фразеологічний (25K entries) — Ukrainian idioms and expressions
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets) — synonyms, antonyms
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries) — English→Ukrainian translations

## Dictionaries (local, in RAG or SQLite)

| Dictionary | Entries | Type | Collection/File |
|-----------|---------|------|-----------------|
| **VESUM** | 409K lemmas, 6.7M forms | Morphological (POS, gender, inflections) | `data/vesum.db` (SQLite) |
| **СУМ-11** | 127K | Ukrainian explanatory (definitions, citations) | `data/sum11/chunks.jsonl` → RAG |
| **Грінченко** | 67K | Historical Ukrainian (1907, etymology) | `grinchenko_dict` (RAG) |
| **Балла EN→UK** | 79K | English→Ukrainian translations | `data/balla-en-uk/chunks.jsonl` → RAG |
| **Антоненко-Давидович** | 279 | Style guide (calques, Russianisms) | `style_guide` (RAG) |
| **Фразеологічний** | 25K | Ukrainian idioms and expressions | `data/frazeolohichnyi/chunks.jsonl` → RAG |
| **Stress dictionary** | 2.7M forms | Word stress for annotation | via `ukrainian-word-stress` |

Source: [bakustarver/ukr-dictionaries-list-opensource](https://github.com/bakustarver/ukr-dictionaries-list-opensource) (СУМ-11, Балла, Фразеологічний)
