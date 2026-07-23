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
- `mcp__sources__verify_word` / `mcp__sources__verify_words` / `mcp__sources__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Also surfaces `is_archaic` and `has_archaic_forms` metadata flags for forms tagged as historical.
- `mcp__sources__check_modern_form` — VESUM metadata extraction to explicitly check if a word has modern codified forms vs only archaic forms.
- `mcp__sources__search_sources` — **PREFERRED unified entry point** across textbooks, literary corpora, Wikipedia, external articles, and `ukrainian_wiki`
- `mcp__sources__search_text` — textbook content search (23K chunks, Grades 1-11)
- `mcp__sources__search_images` — textbook image search (14K images)
- `mcp__sources__search_literary` — primary literary sources (125K chunks — chronicles, poetry, legal texts)
- `mcp__sources__query_pravopys` — Ukrainian orthography rules (Правопис 2019)
- `mcp__sources__query_wikipedia` — Ukrainian Wikipedia
- `mcp__sources__search_heritage` — **canonical heritage-defense lookup** for verifying potential archaisms, historisms, dialectisms, and inherited Ukrainian words against Russianism/surzhyk false positives. Merges Грінченко, ЕСУМ, slovnyk.me, and Антоненко-Давидович evidence.

> Start with `mcp__sources__search_sources` for general retrieval. Keep `mcp__sources__search_text` for explicit textbook-only scoping when you do not want literary, Wikipedia, external, or `ukrainian_wiki` results mixed in.
>
> **Note on graceful degradation**: Dense reranking inside `mcp__sources__search_sources` is a degradable enhancement. On systems under 32GB RAM or if `SOURCES_MCP_NO_MLX=1` is specified, the MLX embedding worker will not auto-spawn, and search queries will degrade gracefully and silently to standard SQLite FTS5-only ranking instead of raising an exception.


## Dictionary tools (for quality and vocabulary)
- `mcp__sources__check_russian_shadow` — Detects Russian-pattern morphology (Surzhyk / false forms) in Ukrainian text without ingesting Russian text. Uses `pymorphy3` heuristic modeling.
- `mcp__sources__search_ua_gec_errors` — UA-GEC (Ukrainian Grammatical Error Corpus, Grammarly UA team, MIT). Returns human-annotated error→correction pairs from 8,937 rows, filtered to russianism-relevant tags (F/Calque, F/Collocation, G/Case, G/Gender). Highest-signal evidence for register/phraseological calques that aren't in Antonenko. Pair with `search_style_guide` (structured Antonenko) and `search_text source=antonenko-davydovych-yak-my-hovorymo` (full-text Antonenko prose) for the complete russianism evidence layer.
- `mcp__sources__search_style_guide` — Антоненко-Давидович **structured entries** (342 keyed headwords). **Calques and Russianisms.** HIGH PRIORITY. **Pair with `mcp__sources__search_text` against `source_file='antonenko-davydovych-yak-my-hovorymo'`** to also search the **full-book prose corpus (169 chunks)** — the structured index misses extensive rules, examples, and discussion present in the prose. For any Russianism verification, **query BOTH**: a phrase absent from `style_guide` may still be condemned in the prose body. Failing to do so was the H1 prompt bug (`audit/2026-05-17-judge-calibration-h1/COMPARISON.md`) — F1 collapsed because retrieval only hit the structured 342.
- `mcp__sources__query_cefr_level` — PULS CEFR vocabulary (5.9K words, A1-C1) — check level-appropriateness
- `mcp__sources__search_definitions` — СУМ-11 (127K entries) — Ukrainian explanatory dictionary. **⚠️ Partially Sovietized for ideological terms** — see "Sovietization caveat" below. Each result row carries `sovietization_risk` (0/1/2) and `sovietization_keywords`.
- `mcp__sources__search_grinchenko_1907` — Грінченко (67K entries) — historical Ukrainian dictionary from 1907. Use for pre-Soviet usage attestation; **NOT for word origins/etymology** — that's a separate concern handled by `search_esum` below.
- `mcp__sources__search_esum` — ЕСУМ etymological dictionary — canonical name for ЕСУМ. Coverage: all 6 volumes (А–Я), ~36K entries (vols 1–6 fully ingested). Optional `volume` filter (1–6); omit to search all. Falls back to a goroh.pp.ua hint if word not found.
- `mcp__sources__search_slovnyk_me` — slovnyk.me single-source aggregator. Uses curated `sources.db` rows when present and optional live direct-entry `/dict/{slug}/{word}` fallback. Returns URL, dictionary slug, bounded snippet, `is_modern`, `is_dialect`, `is_russianism`, and `sovietization_risk`. Use when slovnyk.me specifically is required; prefer `search_heritage` for archaism-vs-Russianism decisions.
- `mcp__sources__search_idioms` — Фразеологічний (25K entries) — Ukrainian idioms and expressions
- `mcp__sources__search_synonyms` — Ukrajinet WordNet (122K synsets) — synonyms, antonyms. **⚠️ Synsets are largely auto-translated from Open English WordNet** per upstream README — quality audit pending (#1657 Tier 3).
- `mcp__sources__translate_en_uk` — Балла EN→UK (79K entries) — English→Ukrainian translations. One-way only; UK→EN reverse not yet built.

## Heritage defense

Use `mcp__sources__search_heritage` when a word may be an authentic Ukrainian
archaism, historism, dialectism, regionalism, or contact borrowing rather than a
Russianism/surzhyk form.

The merger is intentionally conservative:

- Pre-Soviet Грінченко evidence ranks highest.
- ЕСУМ etymology ranks next, especially with Proto-Slavic cognate markers.
- slovnyk.me СУМ-20/regional dictionaries provide modern and regional
  attestation without duplicating the existing Грінченко/ЕСУМ tables.
- Антоненко-Давидович style-guide hits are included as warnings but demoted;
  a warning does not erase stronger historical or etymological evidence.
- slovnyk.me dictionaries that duplicate canonical local tools are blocked in
  `search_slovnyk_me`: use `search_definitions`, `search_grinchenko_1907`,
  `search_style_guide`, `search_idioms`, or `translate_en_uk` instead.

For writer/reviewer prompts: call `search_heritage` before rejecting an
unfamiliar Ukrainian-looking word as Russianism. The load-bearing example is
`кобета`/`кобіта`: the tool surfaces Lviv/regional and СУМ-20 evidence and keeps
`is_russianism=false`.

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
- Prefer `search_heritage` for an evidence merge, or `search_slovnyk_me` /
  slovnyk.me `newsum` (СУМ-20) for a modern definitional baseline.
- If neither alternative is available, paraphrase neutrally and flag in
  reviewer evidence.

СУМ-20 rows are cleaner on sampled neutral words, but not assumed categorically
clean. `search_slovnyk_me` applies the same `sovietization_risk` /
`sovietization_keywords` classifier to slovnyk.me rows.

The scan is reproducible:
`.venv/bin/python scripts/audit/sum11_sovietization_scan.py --db data/sources.db`.
Audit report at `audit/sum11_sovietization_scan_<DATE>.md`.

## Dictionaries (local, in sources.db or SQLite)

| Dictionary | Entries | Type | Collection/File |
|-----------|---------|------|-----------------|
| **VESUM** | 409K lemmas, 6.7M forms | Morphological (POS, gender, inflections) | `data/vesum.db` (SQLite) |
| **UA-GEC** | 8.9K high-signal pairs | Human-annotated errors (calques, cases, etc.) | `data/sources.db` FTS5 |
| **СУМ-11** | 127K (7,152 flagged Sovietized — #1659) | Ukrainian explanatory (definitions, citations) | `data/sources.db` FTS5 |
| **Грінченко** | 67K | Historical Ukrainian (1907, lexicographic) | `data/sources.db` FTS5 |
| **ЕСУМ** | 36K entries, vols 1–6 (А–Я) | Etymological dictionary | `data/sources.db` FTS5 via `search_esum` |
| **slovnyk.me** | bounded per-word rows + live direct lookup | Modern/regional dictionary aggregator; no bulk mirror | `data/sources.db` `slovnyk_me_entries` + live `/dict/{slug}/{word}` |
| **Балла EN→UK** | 79K | English→Ukrainian translations | `data/sources.db` FTS5 |
| **Антоненко-Давидович** | 342 structured + 169 prose chunks | Style guide (calques, Russianisms) — `style_guide` table (keyed entries) + `textbooks` table (source_file=`antonenko-davydovych-yak-my-hovorymo`, full-book prose) | `data/sources.db` FTS5 |
| **Фразеологічний** | 25K | Ukrainian idioms and expressions | `data/sources.db` FTS5 |
| **Stress dictionary** | 2.7M forms | Word stress for annotation | via `ukrainian-word-stress` |

Source: [bakustarver/ukr-dictionaries-list-opensource](https://github.com/bakustarver/ukr-dictionaries-list-opensource) (СУМ-11, Балла, Фразеологічний)
