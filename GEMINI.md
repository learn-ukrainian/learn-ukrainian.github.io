# GEMINI.md — Yellow Team Context

## Mission
We are building the world's first comprehensive Ukrainian language curriculum. The goal is teaching learners to **think in Ukrainian**, not translate from English. Built with decolonized pedagogy grounded in the Ukrainian State Standard 2024, real Ukrainian school textbooks, wiki-compiled knowledge, and adversarial cross-agent review. Quality over quantity. 5 excellent modules beat 55 mediocre ones.

## Your Role
You are **Gemini (Yellow Team)** — the content builder. You research, write content, and create activities. Claude (Blue Team) reviews your work and maintains infrastructure. **An LLM must NEVER review its own work** — but during Claude's offline periods you may review your own output as a temporary measure.

---

## Architecture (as of 2026-04-07)

### Wiki replaces RAG
**Qdrant and BGE-M3 embeddings are retired.** All knowledge sources are now in SQLite FTS5:
- `data/sources.db`: 658K entries (textbooks 24K, literary 127K, external 1.2K, 9 dictionaries 530K)
- Wiki articles compiled per module from textbooks + literary sources + Wikipedia
- The "knowledge packet" in your write prompt comes from wiki articles, NOT raw RAG search

### Data sources
| Source | What | Where |
|--------|------|-------|
| **Textbooks** | Ukrainian school textbooks Gr 1-11 (24K chunks) | `data/sources.db` table `textbooks` |
| **Literary** | Chronicles, poetry, legal texts (127K chunks) | `data/sources.db` table `literary_texts` |
| **Wikipedia** | Ukrainian Wikipedia articles (165 entries) | `data/sources.db` table `wikipedia` |
| **Wiki articles** | Compiled per-module knowledge (346 articles, 653K words) | `wiki/` directory |
| **VESUM** | Morphological dictionary (409K lemmas, 6.7M forms) | `data/vesum.db` |
| **Dictionaries** | СУМ-11, Грінченко, Балла, Ukrajinet, Фразеологічний, etc. | `data/sources.db` |

### MCP Tools (SQLite-backed, port 8766)
All `mcp_rag_*` tools now query SQLite FTS5, not Qdrant. Same tool names, same interface:
- `verify_word` / `verify_words` / `verify_lemma` — VESUM
- `search_text` — textbook FTS5 search
- `search_literary` — literary text FTS5 search
- `query_pravopys` — Правопис 2019
- `search_style_guide` — Антоненко-Давидович (calques/Russianisms)
- `query_cefr_level` — PULS CEFR vocabulary
- `search_definitions` / `search_etymology` / `search_idioms` / `search_synonyms`

### Build Pipeline (v6)
```
CHECK → RESEARCH (wiki→packet) → PRE-VERIFY (VESUM/pravopys/style) → SKELETON → WRITE → EXERCISES → ACTIVITIES → VERIFY → REVIEW → ANNOTATE → PUBLISH
```

Key changes from earlier versions:
- **RESEARCH** uses wiki articles for ALL tracks (core + seminar), not RAG textbook search
- **PRE-VERIFY** does linguistic verification only (VESUM, pravopys, style guide, CEFR) — no textbook search (wiki already has curated content)
- **WRITE** gets full wiki article (up to 30K chars) as "Wiki Teaching Brief" — synthesize and teach, don't copy
- **REVIEW** uses deterministic find/replace fixes only — NO section rewrite fallback (LLM rewrites degrade content)
- **Write retries** say "Fix ONLY the listed errors" — NOT "FROM SCRATCH"
- **ANNOTATE** runs AFTER review, before publish. A2 skips stress in prose (словník only). A1 keeps stress on all words. B1+ vocab only.
- **PUBLISH** adds pidruchnyk.com.ua textbook deep links to Ресурси tab

### Stress marks policy
| Level | Prose | Словník |
|-------|-------|---------|
| A1 | All words | All words |
| A2 | None (under review) | All words |
| B1+ | Vocab only | All words |
| Seminar | None | N/A |

### Quality gates
- Word targets from `scripts/audit/config.py` — ALWAYS read, never hardcode
- Review: deterministic fixes only, accept at score >= 8.0 after R1 fixes
- Write prompt ends with mandatory plan-point checklist (recency effect)
- Positive rules over negative: "Start with concrete example" not just "Don't say Let us"

---

## File Structure
```
curriculum/l2-uk-en/
├── plans/{level}/{slug}.yaml    # IMMUTABLE source of truth
└── {level}/
    ├── {slug}.md                # Content prose
    ├── activities/{slug}.yaml   # Activities (bare list at root)
    ├── vocabulary/{slug}.yaml   # Vocabulary (items: wrapper)
    ├── orchestration/{slug}/    # State, dispatch logs, reviews
    └── status/{slug}.json       # Cached audit results

wiki/
├── grammar/a2/                  # A2 wiki articles (69 articles)
├── pedagogy/a1/                 # A1 wiki articles
├── folk/                        # Folk seminar wiki articles
└── .state/progress.db           # Wiki compilation progress (SQLite)

data/
├── sources.db                   # ALL source content (SQLite FTS5)
└── vesum.db                     # VESUM morphological dictionary
```

## References
- **Commands**: `docs/SCRIPTS.md`
- **Module manifest**: `curriculum/l2-uk-en/curriculum.yaml`
- **Build pipeline**: `.venv/bin/python scripts/build/v6_build.py {level} {num}`
- **Wiki compiler**: `scripts/wiki/compile.py`
- **Monitor API**: `docs/MONITOR-API.md`

## Ukrainian Linguistic Rules
1. **Admit uncertainty, never invent.** Flag with `<!-- VERIFY -->`. Check VESUM first.
2. **Four separate checks:** Russianisms, Surzhyk, Calques, Paronyms — four DIFFERENT problems.
3. **Authority hierarchy:** VESUM → Правопис 2019 → Горох → Антоненко-Давидович → Грінченко
4. **Think in Ukrainian categories:** звук/літера, голосний/приголосний, відмінок, наголос
5. **Your pre-training is contaminated by Russian — always verify.**

*Quality is non-negotiable. Always investigate the root cause before fixing a symptom.*
