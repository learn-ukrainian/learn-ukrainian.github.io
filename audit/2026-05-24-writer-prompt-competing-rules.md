I completed the read-only audit, but I could not create `audit/2026-05-24-writer-prompt-competing-rules.md`: the required `touch` failed with `Operation not permitted` in this sandbox.

- Found **5 direct competing rules** in `linear-write.md`; the smoking gun is `linear-write.md:455`, which still tells the writer to run `search_text` for each `plan_references` entry, directly contradicting `#R-TEXTBOOK-30W` Step A.
- Build #6’s Knowledge Packet **does include Grade 4 textbook anchors outside the plan**: `knowledge_packet.md:234` lists `S1=4-klas-ukrmova-zaharijchuk_s1922`, Grade 4 p.150, while plan references are only Grade 1 p.24 and p.52.
- `resources.yaml` schema is permissive pre-emit: `linear_pipeline.py:504-526` requires only `title` and `role`, allows optional `packet_chunk_id`/`chunk_id`, and does not enforce plan-reference membership.

Recommended minimal fixes:
1. Add an early citation-authority hierarchy after `linear-write.md:99`.
2. Replace `linear-write.md:193` so Knowledge Packet anchors cannot become textbook entries in `resources.yaml`.
3. Replace `linear-write.md:455` with the same chunk-id-first rule as `#R-TEXTBOOK-30W`, including the Grade 1 vs Grade 4 example.

The retained artifacts also confirm the behavior: `resources.yaml:13-17` contains the out-of-plan Grade 4 entry, `writer_tool_calls.json:3-30` shows `search_text` calls for p.24/p.52 and no `get_chunk_context`, and `python_qg.json:83-111` records both `citations_resolve` and `textbook_grounding` failures.
