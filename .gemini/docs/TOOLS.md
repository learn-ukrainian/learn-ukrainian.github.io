# RAG Tools (MCP) & Dictionaries

These tools are available via MCP (in my native tool definitions). ALWAYS use them to verify facts, vocabulary, and grammar.

## Core Linguistic & Content Tools
| Tool | Purpose | Example |
|------|---------|---------|
| `mcp_rag_verify_word` / `verify_words` | Check VESUM morphological dictionary (409K lemmas, 6.7M forms) for word existence, POS, and gender. | `verify_words(["книга", "великий"])` |
| `mcp_rag_verify_lemma` | Get all inflected forms of a word. | `verify_lemma("книга")` |
| `mcp_rag_query_pravopys` | Official Ukrainian orthography rules (Правопис 2019). | `query_pravopys("апостроф")` |
| `mcp_rag_search_text` | Search Ukrainian school textbooks (1.2K+ chunks, Grades 1-11). | `search_text("знахідний відмінок", grade=3)` |
| `mcp_rag_search_images` | Textbook image search (10K+ images). | `search_images("дієслово таблиця")` |
| `mcp_rag_search_literary` | Primary literary sources (chronicles, poetry, legal texts). | `search_literary("Шевченко Заповіт")` |
| `mcp_rag_query_grac` | Check word/phrase frequency (corpus data). | `query_grac("залюбки")` |
| `mcp_rag_query_wikipedia` | Ukrainian Wikipedia (modes: summary, full, search, sections, links). | `query_wikipedia("Данило Галицький", mode="summary")` |
| `mcp_rag_query_r2u` | Russian-Ukrainian dictionary (for finding Ukrainian equivalents). | `query_r2u("красивый")` |
| `mcp_rag_query_ulif` | ULIF linguistic dictionary. | `query_ulif("наголос")` |

## Specialized Dictionaries (for quality and vocabulary)
- `mcp_rag_search_style_guide` — Антоненко-Давидович (279 entries) — **calques and Russianisms**. HIGH PRIORITY.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words, A1-C1) — check level-appropriateness
- `mcp_rag_search_definitions` — СУМ-11 (127K entries) — Ukrainian explanatory dictionary
- `mcp_rag_search_etymology` — Грінченко (67K entries) — historical dictionary, etymology
- `mcp_rag_search_idioms` — Фразеологічний (25K entries) — Ukrainian idioms and expressions
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets) — synonyms, antonyms
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries) — English→Ukrainian translations

## Infrastructure & APIs
| Component | What |
|-----------|------|
| **Monitor API** | `http://localhost:8765` — FastAPI server with 30+ endpoints. **Use this first, not grep.** Full docs: `docs/MONITOR-API.md` |
| **Module dashboard** | `scripts/module_dashboard.py` — aggregated module health (also available via API) |
| **Audit system** | `scripts/audit_module.py` — deterministic quality gates |
| **Build pipeline v6** | `scripts/build/v6_build.py` — research → discover → content → validate → activities → review → mdx |

### Monitor API — Key Endpoints
**Session start:**
- `GET /api/state/summary` — full project snapshot
- `GET /api/state/failing` — all failing modules across all tracks
- `GET /api/state/issues?severity=critical` — critical issues to fix now
- `GET /api/state/track-health/{track}` — track overview (build, audit, review)

**Module deep-dive:**
- `GET /api/state/module/{track}/{num}` — everything about one module
- `GET /api/state/weak-points` — quality issues sorted worst-first
