# ADR-006: Multi-tier compile-layer retrieval architecture

**Status**: Accepted
**Date**: 2026-04-19
**Related**: #1335 (epic), #1330 (diagnostic), #1101 (benchmark), ADR-005 (partially superseded), #1337, #1338, #1339, #1340, #1341, #1342

## Context

The COMPILE-layer retrieval pipeline is the bottleneck for wiki generation quality. `#1330` established the failure mode on `wiki/pedagogy/a1/sounds-letters-and-hello.md`: only 5/10 target concepts surfaced into the 40 returned chunks, while 4/10 concepts were present elsewhere in the corpus and were never surfaced at all.

The benchmark evidence in `#1101` shows this problem is tier-dependent rather than project-wide. Dense retrieval reached Recall@10 of 0.967 on modern Ukrainian textbooks, but only 0.600 on Middle Ukrainian and 0.400 on Old East Slavic. Hybrid retrieval was strictly worse than dense on the archaic tiers, so the data does not support dense+sparse as a universal strategy.

This ADR follows the scaling argument in Andrej Karpathy's "Software in the era of AI" discussion of search at compile/lookup time rather than at consumption time: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>. ADR-005's wiki-as-consumption-unit decision remains correct at the WRITE layer; the correction here is limited to how sources are retrieved during wiki compilation.

## Decision

Split COMPILE-layer retrieval by linguistic tier instead of enforcing one retrieval strategy project-wide.

- **T1-T2 (modern Ukrainian)**: A1, A2, B1, B2, C1, C2, plus seminars HIST, BIO, ISTORIO, and LIT, use section/chapter-level FTS5 retrieval with a dense re-ranker, parent-context injection, and grade routing.
- **T3 (RUTH / Middle Ukrainian)**: use section/work-level metadata routing only. No dense retrieval. No hybrid retrieval.
- **T4 (OES / Old East Slavic)**: use section/work-level metadata routing only. No dense retrieval. No hybrid retrieval.
- **Hybrid retrieval is rejected everywhere**: dense+sparse combinations are not part of the architecture for any tier.
- **Embedder selection is deferred**: `#1343` is the active bakeoff, and this ADR does not lock the project to a specific embedder.

## Alternatives considered

- **Pure SQLite FTS5 keyword bakeoff (Meilisearch / pg_trgm / OpenSearch-Snowball)**: rejected because it addresses morphological variance, not the actual lexical-disjoint miss profile observed in `#1330`.
- **Pure dense embeddings project-wide**: rejected because it breaks T3-T4 retrieval quality.
- **Live RAG at WRITE phase**: rejected because ADR-005 stands; wiki articles remain the consumption unit.
- **Hybrid (dense + sparse) retrieval**: rejected because `#1101` shows zero benefit on modern tiers and active harm on archaic tiers.
- **Deferring any change until a full embedder bakeoff**: rejected because the unit-size and routing fix is primary and independent of the eventual embedder winner.

## Consequences

**Positive**:
- Closes the retrieval failure mode exposed by `#1330`.
- Preserves ADR-005's wiki-as-consumption-unit architecture at the WRITE layer.
- Makes grade routing an enforceable part of the T1-T2 compile pipeline; `#1339` is the supporting bug fix.

**Negative / risks**:
- Introduces parent-section schema work tracked in `#1337`.
- Requires dense-embedder inference during compile time for T1-T2.
- Adds a permanent tier classification requirement for each source.

## Implementation tickets

- `#1337` — schema: parent section table + extraction pipeline
- `#1338` — T1-T2 retrieval pipeline
- `#1339` — grade-filter bug fix (closed)
- `#1340` — re-validation against the `#1330` diagnostic
- `#1341` — T3-T4 retrieval pipeline
- `#1342` — documentation updates and epic closeout

## Discussion record

- `reviews` channel, thread `ae74c96384514d47ba81417e6e8c0da6` — converged architecture, round 2
- `reviews` channel, thread `0d9b884ecfe94db8bd9bd681a9c5fe49` — round 1, bakeoff vs query construction

These threads record the Claude + Codex + Gemini discussion rounds and end with all participants at `[AGREE]`.

Tail command for future readers: `.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail reviews --thread <ID>`
