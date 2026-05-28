---
id: R-CITE-HONEST
description: Use real sources only; verify attribution; quotes must pass verify_quote.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: []
---

Use real sources only. Grammar/cultural claims need attributed, MCP-groundable evidence; ghost references fail `citations_resolve`. Use `mcp__sources__verify_source_attribution(source, claim)` for dictionary/style-guide/author claims and do not cite when `discusses=false`.

Сибір case study (May 2026): a prior answer fabricated a Грінченко citation, an Антоненко-Давидович claim, and a fused Shevchenko line. Verify before citing; do not ship authority theatre.

**Source-citation discipline** (citation honesty). Use `mcp__sources__verify_source_attribution(source, claim)` for dictionary/style-guide/source claims. If `discusses=false`, do not cite. Every grammar claim must be grounded in the Knowledge Packet or a retrieved textbook/source chunk.

**Grammar claim grounding.** EVERY specific grammar claim (rules about aspect, case endings, syntax, phonetics, morphology, word formation, stress/prosody, orthography, or learner-facing meaning distinctions) MUST cite an authoritative source from the Knowledge Packet or a specific school textbook. Name the source in the text or as an HTML comment with concrete metadata: `<!-- VERIFY: source="..." grade="..." author="..." -->`. If it's a new rule not verbatim in the packet, verify it via `mcp__sources__search_text` and cite the exact grade and author.

Sources in blockquotes/resources must be either in `plan_references` or grounded in a Knowledge Packet / `search_text` result that appears in writer telemetry, EXCEPT `resources.yaml` entries with `role: textbook`: those come ONLY from `plan.references`. Every textbook-role resource MUST carry the plan chunk_id in `packet_chunk_id`, `chunk_id`, or `notes`, and that chunk_id MUST appear literally in `plan.references[*].notes`. Knowledge Packet anchors and out-of-plan `search_text` results may support understanding, but they MUST NOT become textbook entries in `resources.yaml`.

**Quote attribution discipline.** Every attributed Ukrainian quote must pass `mcp__sources__verify_quote(author, text)` with `matched=true` and `best_confidence >= 0.85`. Never fuse snippets from separate sources.
