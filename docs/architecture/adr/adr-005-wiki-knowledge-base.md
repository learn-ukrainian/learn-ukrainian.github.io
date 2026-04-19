# ADR-005: Wiki knowledge base — pre-compiled articles replace live RAG for seminar writes

> **Note (2026-04-19)**: The "SQLite FTS5, not Qdrant" decision is correct for
> WRITE-layer retrieval and for T3-T4 (RUTH/OES) compile-layer retrieval. For
> T1-T2 (modern Ukrainian) compile-layer retrieval, see ADR-006 — `#1101`
> benchmark data showed dense embeddings hit 0.967 Recall@10 on modern
> textbooks, and ADR-005's project-wide retirement of dense was over-broad.

**Status**: Accepted
**Date**: 2026-04-06 (landed) / 2026-04-11 (recorded)
**Related**: #1129 (epic), #1136, #1161, #1171, `scripts/wiki/`, `docs/best-practices/track-architecture.md`

## Context

Seminar modules (HIST, BIO, LIT, OES, RUTH, FOLK, ISTORIO) require 5000+ words of deeply-researched prose grounded in primary sources. Early approaches used live RAG search during the `write` phase: the writer would query Qdrant/MCP for relevant chunks on every call. This had three fatal problems:

1. **Latency**: Each live RAG query added 2-5 seconds. Multiply by 8+ queries per module write call, times multiple retries, times hundreds of modules — the seminar build budget blew up.
2. **Non-determinism**: Same prompt, different results depending on Qdrant's embedding cache state. Re-running a build produced different source citations, which meant the reviewer couldn't reliably check the writer's work.
3. **Source quality mixing**: Raw RAG results mixed high-quality textbook chunks with low-quality YouTube transcripts and Wikipedia paraphrases. The writer had no way to weight them and often cited the weakest source because it appeared first in the retrieval ranking.

The existing dense RAG index worked for short A1/A2 grammar lookups ("how is the genitive formed?") but failed for the kind of research synthesis seminar tracks need.

## Decision

Introduce a **wiki layer** at `wiki/` with pre-compiled reference articles. Each article is:

- Generated once by Gemini via `scripts/wiki/compile.py` using a track-specific prompt (`compile_pedagogy_brief.md`, `compile_grammar_brief.md`, `compile_academic.md`, `compile_article.md`)
- Source-cited at chunk-level: every claim must cite `(Source N: {chunk_id})` where `chunk_id` is the actual SQLite FTS5 row ID in `data/sources.db`
- Quality-gated by `scripts/wiki/quality_gate.py` before use
- Consumed by the seminar write phase as a single pre-baked context block ("knowledge packet") instead of live RAG queries

**Architecture**:

```
data/sources.db (SQLite FTS5)       scripts/wiki/compile.py
      ↓                                       ↓
Textbooks (23K chunks)           Gemini compiles article
Literary (125K chunks)    →      using track-specific prompt
External (1.2K entries)                       ↓
Wikipedia + 9 dictionaries      wiki/{domain}/{slug}.md
                                              ↓
                                v6 write phase injects packet
```

**Key design choices**:
- **SQLite FTS5, not Qdrant**: after benchmarking, dense embeddings hurt recall on Old East Slavic / Middle Ukrainian literary texts (see #1101). Full-text search over our curated source set outperformed hybrid for the specific retrieval patterns wiki compilation needs. Qdrant was retired.
- **Compile once, serve many**: wiki articles are frozen after passing the quality gate. Multiple seminar modules sharing the same topic (e.g. Khmelnytskyi, Kyivan Rus) read the SAME wiki article, guaranteeing consistency across modules.
- **Chunk-ID citations are mandatory**: the `_format_sources` function in `scripts/wiki/compiler.py` injects `Chunk ID: {id}` into every source block so the writer can cite it verbatim. The #1161 prompt rewrite made chunk-ID citations a hard requirement.
- **Quality gate before use**: `scripts/wiki/quality_gate.py` checks for short articles, AI-leaked thinking, missing headings, and fence wrapping. Articles that fail the gate are deleted and recompiled via `--force`.

Wiki article review is a single-pass scoring operation (#1169 disabled the rewrite loop because empirical data showed 0/5 rewrites improved scores and 5/5 degraded them). Low-scoring articles are logged for `--force` recompile; there is no iterative polish loop.

## Alternatives considered

- **Live RAG during write** (the previous approach) → rejected: non-deterministic, slow, mixed source quality.
- **Hybrid RAG (Qdrant dense + BM25 sparse)** → rejected: benchmark data (#1101) showed sparse retrieval degraded recall on literary texts by 10-13%. Dense-only was better than hybrid for our corpus.
- **Dense Qdrant + manual source curation** → rejected: the "curation" is exactly what the wiki system does, but structured so one LLM call produces the curated context instead of requiring human source-picking per module.
- **Embed ALL textbook + literary chunks directly in writer prompts** (no wiki layer) → rejected: the context budget is 30K chars per write phase; 660K source entries won't fit. Wiki articles are 2-5K chars each — ~6 per module — which fits.

## Consequences

**Positive**:
- Seminar write calls are deterministic: same module + same plan = same citations, run after run.
- Wiki articles are auditable. A reviewer can open `wiki/grammar/b2/active-participles-past.md` and check every claim against its cited chunk_id without talking to an LLM.
- Cross-module consistency: the Kyivan Rus wiki article is the single source of truth for every HIST module that references that period. Update the article, and the next build of every dependent module picks up the change automatically via rebuild.
- The monitor API (#1171) exposes wiki status at `/api/wiki/*`, making compilation progress visible without CLI shelling.

**Negative / risks**:
- Wiki compilation itself is a non-trivial pipeline step. Each article takes 2-4 minutes to compile via Gemini. There are currently 900+ articles pending compilation across HIST (140), BIO (180), ISTORIO (136), LIT (232+), OES (102), RUTH (115), FOLK (27 done). Full compilation is a multi-day batch job.
- Wiki articles can go stale. Source updates (new textbook editions, new primary sources) require recompiling affected articles. We currently have no automatic invalidation — compilation is manual via `--force`.
- The quality floor is now the wiki compilation prompt, not the write prompt. The #1161 rewrite of all four compile prompts was specifically to raise the wiki quality baseline from 7.7/10 to 9+/10.

**Neutral / follow-ups**:
- Wiki compilation is its own epic (#1129) with sub-issues per track. Completion requires ongoing batch runs.
- Wiki articles are currently read directly from the filesystem by the seminar build. A future optimization could cache them in a searchable index, but current performance is fine (file reads are trivial compared to LLM calls).

## Verification

- `scripts/wiki/quality_gate.py` — runs across compiled articles, surfaces issues
- `tests/test_wiki_*.py` — parser, compiler, state, sources tests (some still have pre-existing failures unrelated to this ADR)
- Monitor API: `GET /api/wiki/status` — per-track compiled vs total
- Build integration: seminar modules using pre-compiled wiki articles can be seen in `scripts/build/v6_build.py::_build_seminar_packet` (exists as a helper, pre-existing test failures in `test_wiki_pipeline_integration.py` are for a different legacy function and not this ADR's scope)
