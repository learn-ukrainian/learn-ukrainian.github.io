# Decision: Evidence pack replaces wiki as LLM research input for core rebuild

- **ID:** dec-015
- **Date:** 2026-09-30
- **Expires:** 2026-12-29
- **Status:** active (operator GO 2026-09-30)
- **Scope:** pipeline
- **Parent:** #7994
- **Issue:** #9278
- **Related:** #8397, #9233, #9279

## Decision

1. **Evidence pack replaces wiki for core rebuild.** For the core A1–B2 rebuild, the per-module evidence pack is the model's research input and replaces the wiki (confirming R-25 and R-26 accepted on 2026-09-21).
2. **The wiki is an LLM-facing artifact, never a human-facing page.** The lessons are the human-facing product. The earlier option in R-25 stating that "a human-readable wiki page may be rendered from the pack" is removed entirely, not reworded.
3. **No wiki generated for core modules.** Open question Q10 ("one wiki packet per module") is resolved as "no". No wiki packets or pages are generated for core modules.
4. **Existing wiki preserved for V7 tracks.** The existing wiki remains the LLM research input only for tracks still operating on the V7 pipeline (such as seminars), until each track migrates to the fresh-build engine. No existing wiki content is deleted.
5. **Search method for building packs under evaluation in #9233.** The search method for building packs is under evaluation in #9233 (exact-form FTS5 vs lemma-aware FTS vs embedder + reranker; the model choice is the operator's). Until that decision, packs are built with the keyword (FTS5) sources tools. #9279 fixes `search_sources` ranking when no dense index exists.

## Context

The fresh-build requirements document (`docs/epics/fresh-build-requirements.md`) contained internal contradictions:
- R-10 stated that the engine builds from "the plan, the wiki and the MCP", while R-25 and R-26 specified that the writer receives only the plan entry, the lesson's pack evidence, and the learner state.
- R-21 stated that the wiki is improved as part of this work.
- R-25 allowed rendering a human-readable wiki page from the pack, confusing an LLM-facing intermediate with a learner-facing product.
- Q10 left open whether to generate a wiki packet per module, and `docs/epics/fresh-build-build-program.md` line 57 listed the Q10 wiki packet as a follow-up.

This decision settles those points into one consistent policy across the core rebuild.

## Alternatives Considered

- **Generate per-module wiki packets for core (Q10 yes):** Rejected. The evidence pack provides structured, corpus-grounded evidence directly to the writer; generating an intermediate wiki for core is redundant and duplicates pack data.
- **Render human-facing wiki pages from evidence packs:** Rejected. The wiki is an LLM-facing artifact, never a human-facing page. The lessons are the human-facing product.

## Consequences

- In `docs/epics/fresh-build-requirements.md`:
  - R-10 states that the engine builds from the plan, the evidence pack, and the MCP.
  - R-21 states that plans, evidence packs, and the build workflow are improved.
  - R-25 removes the sentence allowing a human-readable wiki page to be rendered from the pack.
  - Q10 is resolved as "no wiki is generated for core modules".
- In `docs/epics/fresh-build-build-program.md`: line 57 drops the Q10 follow-up.
- Pipeline code and prompts for core modules do not invoke wiki generation or consume wiki articles.
- Existing wiki files remain untouched in `wiki/` for unmigrated V7 tracks.
