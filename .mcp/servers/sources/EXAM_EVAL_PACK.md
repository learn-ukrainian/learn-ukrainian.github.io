# Sources MCP — exam/eval consumer tool pack

Machine contract for LLM exam/eval harnesses that call Sources MCP tools.
Result schema for pack tools: `sources.tool-result.v1` (see [`TOOL_RESULT_V1.md`](TOOL_RESULT_V1.md)).
Manifest: [`exam_eval_pack.v1.json`](exam_eval_pack.v1.json).

Parent issues: #7957 / epic #7953.

## Dual reading path

1. Call tool → read MCP `structuredContent` (envelope).
2. Assert `schema == "sources.tool-result.v1"`.
3. Branch on `status` (`ok` / `empty` / `error`); for `error` read `error_code`.
4. Use integer `match_count` (and `lemma_count` on verify tools) — never regex prose.
5. On empty FTS with short tokens, inspect `diagnostics.dropped_tokens`.

## Pack tools

| Tool | When to use | Input (high level) | Result schema | Typical failure |
| --- | --- | --- | --- | --- |
| `verify_word` | Attest one surface form in VESUM | `word`, optional `pos_filter` | `sources.tool-result.v1` (+ V4 keys) | `empty` miss; `error` invalid input |
| `verify_words` | Batch morph attestation (prefer over N× `verify_word`) | `words[]`, optional `pos_filter` | same | Partial found; zero hits → `status=empty` |
| `verify_lemma` | Expand lemma → attested forms | `lemma` | same | Empty / invalid lemma |
| `verify_stress` | Stress attestation | stress query args per tool schema | same | Empty / error |
| `check_modern_form` | Modern vs archaic-only forms | `word` | same | Archaic-only → envelope empty triple |
| `search_text` | Textbook FTS chunks | `query`, optional subject/source_file/limit | `sources.tool-result.v1` | Empty; short tokens → `diagnostics.dropped_tokens` |
| `search_literary` | Literary FTS chunks | `query`, optional limit | same | Same empty/diagnostics contract |
| `get_chunk_context` | Fetch one chunk by id | `chunk_id` | same | `error_code=sources_db_missing` / empty |
| `query_pravopys` | Orthography rules | `topic` (text or section number) | same | Empty topic |
| `search_style_guide` | Style guidance (Антоненко-Давидович) | `query` / limit | same | Empty |
| `search_definitions` | СУМ-11 definitions | `query` / limit | same | Empty |
| `search_idioms` | Phraseology | `query` / limit | same | Empty |
| `search_synonyms` | Synonym net | `query` / limit | same | Empty |
| `search_sources` | Unified multi-corpus retrieval | `query`, optional track/limit | same | Empty (never bare `[]`) |

Live `inputSchema` details: Sources MCP `tools/list` (`server.py` `list_tools`).

### `search_sources` — in pack

**Included.** Use for general retrieval when the consumer does not yet know which
corpus owns the evidence. Prefer corpus-specific tools when scoping is known.

## Non-goals (binding)

- No answer keys, held-out items, or scoring rubrics in this pack.
- A hit / `match_count` is **not** an MCQ letter and must not be treated as one.
- Prefer `verify_words` when batching; respect call budgets.
- Do **not** import Learn Ukrainian fleet code into `ukrainian-llm-eval`.
- Public exam content may appear in Sources corpora — treat as contamination risk;
  do not disclose unpublished items via tool logs.

## Related

- Envelope contract: [`TOOL_RESULT_V1.md`](TOOL_RESULT_V1.md)
- Manifest: [`exam_eval_pack.v1.json`](exam_eval_pack.v1.json)
