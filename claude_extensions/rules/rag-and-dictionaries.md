---
paths:
  - "scripts/**"
  - "curriculum/**"
  - "data/**"
---

# RAG Tools (MCP)

Ukrainian language verification and textbook content search:
- `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms)
- `mcp__rag__search_text` — textbook content search (23K chunks, Grades 1-11)
- `mcp__rag__search_images` — textbook image search (14K images)
- `mcp__rag__search_literary` — primary literary sources (125K chunks — chronicles, poetry, legal texts)
- `mcp__rag__query_pravopys` — Ukrainian orthography rules (Правопис 2019)
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia

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
